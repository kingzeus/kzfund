import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List

from flask_apscheduler import APScheduler
from peewee import DatabaseError, IntegrityError

from config import SCHEDULER_CONFIG
from models.database import delete_record, get_record, get_record_list, update_record
from models.task import ModelTask
from scheduler.tasks import TaskFactory, TaskStatus
from kz_dash.utility.singleton import Singleton
from kz_dash.utility.string_helper import get_uuid

# 创建调度器实例
scheduler = APScheduler()
logger = logging.getLogger(__name__)


class TaskExecutionError(Exception):
    """任务执行异常"""


class TaskUpdateError(Exception):
    """任务状态更新异常"""


@Singleton
class JobManager:
    """任务管理器

    主要功能:
    1. 管理任务的生命周期(创建、执行、完成)
    2. 维护任务进度缓存,减少数据库操作
    3. 提供任务状态查询接口
    """

    def __init__(self):
        self.scheduler = scheduler
        self._progress_cache = {}  # {task_id: progress} 任务进度缓存
        logger.debug("初始化任务管理器")

    def init_app(self, app):
        """初始化Flask应用的任务调度器"""
        app.config.update(SCHEDULER_CONFIG)
        self.scheduler.init_app(app)
        self.scheduler.start()
        logger.info("任务调度器初始化成功")
        self.restore_tasks()

    def _update_task_status(self, task: ModelTask):
        """更新任务状态
        1. 如果是普通任务,则直接任务状态设置成完成
        2. 如果是父任务,
            * 如果存在子任务,则根据子任务状态设置状态
            * 根据子任务设置错误信息
        3. 如果存在父任务,则根据子任务状态设置父任务状态
        """

        # 如果存在子任务，则任务状态设置成运行中
        sub_tasks = task.sub_tasks
        if len(sub_tasks) > 0:
            # 统计子任务状态
            sub_task_status_count = {
                TaskStatus.RUNNING: 0,
                TaskStatus.COMPLETED: 0,
                TaskStatus.FAILED: 0,
            }
            for sub_task in sub_tasks:
                if sub_task.status in sub_task_status_count:
                    sub_task_status_count[sub_task.status] += 1

            # 计算任务进度
            # 默认进度10%为任务启动,90%为子任务进度
            task.progress = (
                sub_task_status_count[TaskStatus.COMPLETED]
                + sub_task_status_count[TaskStatus.FAILED]
                + sub_task_status_count[TaskStatus.RUNNING] / 2
            ) * 90 / len(task.sub_tasks) + 10
            if sub_task_status_count[TaskStatus.FAILED] > 0:
                task.status = TaskStatus.FAILED
                task.error = "子任务错误"
            elif sub_task_status_count[TaskStatus.COMPLETED] == len(task.sub_tasks):
                task.status = TaskStatus.COMPLETED
            else:
                task.status = TaskStatus.RUNNING
        else:
            task.status = TaskStatus.COMPLETED

    def _task_wrapper(self, task_type: str, task_id: str, **kwargs):
        """任务执行包装器

        职责:
        1. 更新任务执行状态
        2. 捕获和记录任务异常
        3. 同步任务最终进度到数据库
        """
        try:
            # 更新任务状态为运行中

            task_history = get_record(ModelTask, {"task_id": task_id})

            if not task_history:
                logger.error("任务不存在: %s", task_id)
                raise TaskExecutionError(f"任务不存在: {task_id}")

            task_history.status = TaskStatus.RUNNING
            task_history.start_time = datetime.now()

            logger.info("开始执行任务: %s (ID: %s)", task_type, task_id)

            # 执行具体任务
            try:
                result = TaskFactory().execute_task(task_type, task_id, **kwargs)
            except (ValueError, TypeError) as e:
                raise TaskExecutionError(f"任务参数错误: {str(e)}") from e
            except Exception as e:
                raise TaskExecutionError(f"任务执行失败: {str(e)}") from e

            # 更新任务状态
            self._update_task_status(task_history)
            task_history.result = json.dumps(result, ensure_ascii=False, default=str)

            # 处理父任务
            if task_history.parent_task:
                task_history.save()
                self._update_task_status(task_history.parent_task)
                task_history.parent_task.save()

            logger.info("任务执行更新: %s (ID: %s)->%d%%", task_type, task_id, task_history.progress)

        except TaskExecutionError as e:
            # 任务执行失败
            task_history.status = TaskStatus.FAILED
            task_history.error = str(e)
            logger.error("任务执行失败: %s (ID: %s)", task_type, task_id, exc_info=True)
            raise

        finally:
            # 同步最终状态到数据库
            try:
                # 优先使用缓存中的进度
                if task_id in self._progress_cache:
                    task_history.progress = self._progress_cache[task_id]
                    del self._progress_cache[task_id]
                # 任务完成时设为100%
                elif task_history.status == TaskStatus.COMPLETED:
                    task_history.progress = 100

                task_history.end_time = datetime.now()
                task_history.save()
                logger.debug(
                    "任务最终状态: %s -> status=%s, progress=%s%%",
                    task_id,
                    task_history.status,
                    task_history.progress,
                )
            except (DatabaseError, IntegrityError) as e:
                logger.error("保存任务最终状态失败: %s", str(e))
                raise TaskUpdateError(f"保存任务状态失败: {str(e)}") from e

    def _restore_task(self, task: ModelTask, min_delay: int):
        """恢复任务"""
        restored_count = 0
        # 解析任务参数
        args = json.loads(task.input_params)

        # 单独处理父任务
        if len(task.sub_tasks) > 0:
            # 统计子任务状态
            sub_task_status_count = {
                TaskStatus.RUNNING: 0,
                TaskStatus.PENDING: 0,
            }
            # 优先处理子任务
            for sub_task in task.sub_tasks:
                if sub_task.status in [TaskStatus.RUNNING, TaskStatus.PENDING]:
                    restored_count += self._restore_task(sub_task, min_delay)

            # 统计子任务状态
            for sub_task in task.sub_tasks:
                if sub_task.status in sub_task_status_count:
                    sub_task_status_count[sub_task.status] += 1

            if sub_task_status_count[TaskStatus.PENDING] > 0:
                task.status = TaskStatus.RUNNING
            elif sub_task_status_count[TaskStatus.RUNNING] > 0:
                task.status = TaskStatus.FAILED
                task.error = "子任务超时"
            else:
                task.status = TaskStatus.COMPLETED
            task.save()
        else:
            if task.status == TaskStatus.RUNNING:
                # 如果任务是运行状态,则改成超时失败
                task.status = TaskStatus.FAILED
                task.error = "任务超时"

                task.save()
            elif task.status == TaskStatus.PENDING:
                # 重新添加到调度器
                task.delay = task.delay - min_delay
                if task.delay < 0:
                    task.delay = 0
                task.save()
                self.scheduler.add_job(
                    func=self._task_wrapper,
                    args=(task.type, task.task_id),
                    kwargs=args,
                    id=task.task_id,
                    name=task.name,
                    trigger="date",
                    next_run_time=datetime.now() + timedelta(seconds=task.delay + 1),
                    misfire_grace_time=SCHEDULER_CONFIG["SCHEDULER_JOB_DEFAULTS"][
                        "misfire_grace_time"
                    ],
                )
                restored_count += 1
                logger.debug("恢复任务: %s", task.task_id)
        return restored_count

    def restore_tasks(self):
        """恢复任务

        从数据库中恢复未完成的任务
        """
        try:
            # 查询所有未完成的任务
            unfinished_tasks = get_record_list(
                ModelTask, {"status__in": [TaskStatus.PENDING, TaskStatus.RUNNING]}
            )

            restored_count = 0

            # 获取延迟最小值
            min_delay = 3600
            for task in unfinished_tasks:
                if task.status == TaskStatus.PENDING and task.delay > 0:
                    min_delay = min(min_delay, task.delay)

            for task in unfinished_tasks:
                try:
                    restored_count += self._restore_task(task, min_delay)

                except Exception as e:
                    logger.error("恢复任务失败 %s: %s", task.task_id, str(e), exc_info=True)
                    continue

            if restored_count > 0:
                logger.info("成功恢复 %d 个任务", restored_count)

        except Exception as e:
            logger.error("恢复任务失败: %s", str(e), exc_info=True)

    def add_task(
        self, task_type: str, delay: int = 0, timeout=0, parent_task_id=None, **kwargs
    ) -> str:
        """添加新任务
        为了保证任务正常执行，延时1+delay秒执行

        Args:
            task_type: 任务类型
            delay: 延迟执行时间(秒),默认0秒.
            timeout: 任务超时时间(秒),默认0，采用任务类型对应的默认超时时间
            parent_task_id: 父任务ID
            **kwargs: 任务参数

        Returns:
            task_id: 新创建的任务ID

        Raises:
            ValueError: 任务参数验证失败
        """
        # 验证任务参数
        is_valid, error_message = TaskFactory().validate_task_params(task_type, kwargs)
        if not is_valid:
            logger.error("任务参数验证失败: %s", error_message)
            raise ValueError(error_message)

        task_id = get_uuid()
        task_config = TaskFactory().get_task_types().get(task_type, {})
        if timeout == 0:
            timeout = task_config.get("timeout", SCHEDULER_CONFIG["DEFAULT_TIMEOUT"])

        # 创建任务记录
        update_record(
            ModelTask,
            {"task_id": task_id},
            {
                "parent_task_id": parent_task_id,
                "type": task_type,  # 设置任务类型
                "name": task_config.get("name", task_type),
                "delay": delay,
                "status": TaskStatus.PENDING,
                "timeout": timeout,
                "input_params": json.dumps(kwargs),  # 将参数转换为JSON字符串
            },
        )

        # 添加到调度器立即执行
        self.scheduler.add_job(
            func=self._task_wrapper,
            args=(task_type, task_id),
            kwargs=kwargs,
            id=task_id,
            name=task_config.get("name", task_type),
            trigger="date",
            next_run_time=datetime.now() + timedelta(seconds=delay + 1),
            misfire_grace_time=SCHEDULER_CONFIG["SCHEDULER_JOB_DEFAULTS"]["misfire_grace_time"],
        )

        return task_id

    def copy_task(self, task_id: str) -> str:
        """复制任务"""
        try:
            task = get_record(ModelTask, search_fields={"task_id": task_id})
            if not task:
                logger.error("任务不存在: %s", task_id)
                raise TaskExecutionError(f"任务不存在: {task_id}")

            new_task_id = get_uuid()

            args = json.loads(task.input_params)

            update_record(
                ModelTask,
                {"task_id": new_task_id},
                {
                    "type": task.type,
                    "name": task.name,
                    "delay": task.delay,
                    "status": TaskStatus.PENDING,
                    "timeout": task.timeout,
                    "input_params": task.input_params,
                },
            )
            logger.info("任务复制成功: %s -> %s", task_id, new_task_id)

            # 添加到调度器立即执行
            self.scheduler.add_job(
                func=self._task_wrapper,
                args=(task.type, new_task_id),
                kwargs=args,
                id=new_task_id,
                name=task.name,
                trigger="date",
                misfire_grace_time=SCHEDULER_CONFIG["SCHEDULER_JOB_DEFAULTS"]["misfire_grace_time"],
            )
            return new_task_id
        except (DatabaseError, IntegrityError) as e:
            logger.error("复制任务失败: %s", str(e), exc_info=True)
            return ""

    def update_task_progress(self, task_id: str, progress: int):
        """更新任务进度到缓存"""
        self._progress_cache[task_id] = progress
        logger.debug("更新任务进度缓存: %s -> %d%%", task_id, progress)

    def get_task_progress(self, task_ids: List[str]) -> Dict[str, int]:
        """获取多个任务的进度

        Args:
            task_ids: 任务ID列表

        Returns:
            Dict[str, int]: {task_id: progress} 进度字典
        """
        progress_dict = {}

        # 先从缓存获取
        for task_id in task_ids:
            if task_id in self._progress_cache:
                progress_dict[task_id] = self._progress_cache[task_id]

        # 缓存未命中的从数据库查询
        missing_task_ids = list(set(task_ids) - set(progress_dict.keys()))
        if missing_task_ids:
            try:
                query = ModelTask.select(ModelTask.task_id, ModelTask.progress).where(
                    ModelTask.task_id.in_(missing_task_ids)
                )
                progress_dict.update({task.task_id: task.progress for task in query.execute()})
            except (DatabaseError, IntegrityError) as e:
                logger.error("从数据库获取任务进度失败: %s", str(e))

        return progress_dict

    def _delete_task(self, task: ModelTask):
        """删除指定任务及其所有子任务"""
        try:
            # 1. 获取任务信息
            sub_tasks = task.sub_tasks
            if len(sub_tasks) > 0:
                for sub_task in sub_tasks:
                    self._delete_task(sub_task)

            # 2. 从调度器中移除任务
            if self.scheduler.get_job(task.task_id):
                try:
                    self.scheduler.remove_job(task.task_id)
                except Exception as e:
                    logger.error(f"从调度器移除任务失败 {task.task_id}: {e}")

            # 3. 从数据库中删除任务
            if not delete_record(ModelTask, {"task_id": task.task_id}):
                logger.error(f"从数据库删除任务失败 {task.task_id}")
                raise TaskExecutionError(f"删除任务失败: {task.task_id}")

        except Exception as e:
            logger.error(f"删除任务失败 {task.task_id}: {e}", exc_info=True)
            raise

    def delete_task(self, task_id: str):
        """删除指定任务及其所有子任务

        Args:
            task_id: 要删除的任务ID
        """
        try:
            task = get_record(ModelTask, {"task_id": task_id})
            if not task:
                logger.error("任务不存在: %s", task_id)
                raise TaskExecutionError(f"任务不存在: {task_id}")

            self._delete_task(task)

        except Exception as e:
            logger.error(f"Error deleting task {task_id}: {e}")
            raise e
