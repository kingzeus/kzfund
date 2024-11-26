import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List

from flask_apscheduler import APScheduler
from peewee import DatabaseError, DoesNotExist, IntegrityError

from config import SCHEDULER_CONFIG
from models.task import ModelTask
from scheduler.tasks import TaskFactory, TaskStatus
from utils.singleton import Singleton
from utils.string_helper import get_uuid

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

    def _task_wrapper(self, task_type: str, task_id: str, **kwargs):
        """任务执行包装器

        职责:
        1. 更新任务执行状态
        2. 捕获和记录任务异常
        3. 同步任务最终进度到数据库
        """
        try:
            # 更新任务状态为运行中
            try:
                task_history = ModelTask.get(ModelTask.task_id == task_id)
            except DoesNotExist as exc:
                logger.error("任务不存在: %s", task_id)
                raise TaskExecutionError(f"任务不存在: {task_id}") from exc

            task_history.status = TaskStatus.RUNNING
            task_history.start_time = datetime.now()
            task_history.save()
            logger.info("开始执行任务: %s (ID: %s)", task_type, task_id)

            # 执行具体任务
            try:
                result = TaskFactory().execute_task(task_type, task_id, **kwargs)
            except (ValueError, TypeError) as e:
                raise TaskExecutionError(f"任务参数错误: {str(e)}") from e
            except Exception as e:
                raise TaskExecutionError(f"任务执行失败: {str(e)}") from e

            # 任务成功完成
            task_history.status = TaskStatus.COMPLETED
            task_history.result = str(result)
            logger.info("任务执行完成: %s (ID: %s)", task_type, task_id)

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

    def restore_tasks(self):
        """恢复任务

        从数据库中恢复未完成的任务
        """
        try:
            # 查询所有未完成的任务
            unfinished_tasks = ModelTask.select().where(
                ModelTask.status.in_([TaskStatus.PENDING, TaskStatus.RUNNING])
            )

            restored_count = 0

            # 获取延迟最小值
            min_delay = 3600
            for task in unfinished_tasks:
                if task.status == TaskStatus.PENDING and task.delay > 0:
                    min_delay = min(min_delay, task.delay)

            for task in unfinished_tasks:
                try:
                    # 解析任务参数
                    args = json.loads(task.input_params)

                    args["timeout"] = task.timeout

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

                except Exception as e:
                    logger.error("恢复任务失败 %s: %s", task.task_id, str(e), exc_info=True)
                    continue

            if restored_count > 0:
                logger.info("成功恢复 %d 个任务", restored_count)

        except Exception as e:
            logger.error("恢复任务失败: %s", str(e), exc_info=True)

    def add_task(self, task_type: str, delay: int = 0, parent_task_id=None, **kwargs) -> str:
        """添加新任务
        为了保证任务正常执行，延时1+delay秒执行

        Args:
            task_type: 任务类型
            delay: 延迟执行时间(秒),默认0秒.
            parent_task_id: 父任务ID
            **kwargs: 任务参数(包含 timeout 等)

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

        # 过滤掉已单独保存的参数
        input_params = kwargs.copy()
        input_params.pop("timeout", None)

        # 创建任务记录
        ModelTask.create(
            task_id=task_id,
            parent_task_id=parent_task_id,
            type=task_type,  # 设置任务类型
            name=task_config.get("name", task_type),
            delay=delay,
            status=TaskStatus.PENDING,
            timeout=kwargs.get(
                "timeout",
                task_config.get("timeout", SCHEDULER_CONFIG["DEFAULT_TIMEOUT"]),
            ),
            input_params=json.dumps(input_params),  # 将参数转换为JSON字符串
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
            task = ModelTask.get(ModelTask.task_id == task_id)
            new_task_id = get_uuid()

            args = json.loads(task.input_params)
            args["timeout"] = task.timeout

            ModelTask.create(
                task_id=new_task_id,
                type=task.type,
                name=task.name,
                delay=task.delay,
                status=TaskStatus.PENDING,
                timeout=task.timeout,
                input_params=task.input_params,
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

    def pause_task(self, task_id: str) -> bool:
        """暂停指定任务"""
        try:
            self.scheduler.pause_job(task_id)
            ModelTask.update(status=TaskStatus.PAUSED).where(ModelTask.task_id == task_id).execute()
            logger.info("任务已暂停: %s", task_id)
            return True
        except (DatabaseError, IntegrityError) as e:
            logger.error("暂停任务失败: %s:%s", task_id, str(e), exc_info=True)
            return False

    def resume_task(self, task_id: str) -> bool:
        """恢复已暂停的任务"""
        try:
            self.scheduler.resume_job(task_id)
            ModelTask.update(status=TaskStatus.PENDING).where(
                ModelTask.task_id == task_id
            ).execute()
            logger.info("任务已恢复: %s", task_id)
            return True
        except (DatabaseError, IntegrityError) as e:
            logger.error("恢复任务失败: %s: %s", task_id, str(e), exc_info=True)
            return False

    def get_task_history(self, limit: int = 100) -> List[ModelTask]:
        """获取最近的任务历史记录

        Args:
            limit: 返回的最大记录数,默认100条

        Returns:
            任务历史记录列表,每条记录为ModelTask实例
        """
        try:
            return list(
                ModelTask.select().order_by(ModelTask.created_at.desc()).limit(limit).execute()
            )
        except DatabaseError as e:
            logger.error("获取任务历史记录失败: %s", e)
            return []

    def update_task_progress(self, task_id: str, progress: int):
        """更新任务进度到缓存"""
        self._progress_cache[task_id] = progress
        logger.debug("更新任务进度缓存: %s -> %d%%", task_id, progress)

    def get_tasks_progress(self, task_ids: List[str]) -> Dict[str, int]:
        """获取指定任务的最新进度

        优先从缓存获取,缓存不存在则从数据库读取
        """
        # 优先从缓存获取
        progress_dict = {
            task_id: self._progress_cache[task_id]
            for task_id in task_ids
            if task_id in self._progress_cache
        }

        # 缓存未命中的从数据库获取
        missing_task_ids = [task_id for task_id in task_ids if task_id not in progress_dict]

        if missing_task_ids:
            try:
                query = ModelTask.select(ModelTask.task_id, ModelTask.progress).where(
                    ModelTask.task_id.in_(missing_task_ids)
                )
                progress_dict.update({task.task_id: task.progress for task in query.execute()})
            except (DatabaseError, IntegrityError) as e:
                logger.error("从数据库获取任务进度失败: %s", str(e))

        return progress_dict

    def get_task(self, task_id: str) -> Dict:
        """获取指定任务的详细信息

        Args:
            task_id: 任务ID

        Returns:
            Dict: 包含任务详细信息的字典，如果任务不存在返回 {"status": "not_found"}
        """
        try:
            # 从数据库获取任务信息
            try:
                task = ModelTask.get(ModelTask.task_id == task_id)
            except DoesNotExist:
                logger.warning("任务不存在: %s", task_id)
                return {"status": "not_found"}

            # 获取最新进度
            progress = self._progress_cache.get(task_id, task.progress)

            # 获取任务运行状态
            job = self.scheduler.get_job(task_id)
            current_status = task.status
            if job and task.status == TaskStatus.PENDING:
                current_status = TaskStatus.RUNNING

            return {
                "task_id": task.task_id,
                "name": task.name,
                "delay": task.delay,
                "status": current_status,
                "progress": progress,
                "result": task.result,
                "error": task.error,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "timeout": task.timeout,
                "created_at": task.created_at,
                "input_params": json.loads(task.input_params),
            }

        except (DatabaseError, IntegrityError, DoesNotExist, TypeError, ValueError) as e:
            logger.error("获取任务信息失败: %s, 错误: %s", task_id, str(e), exc_info=True)
            return {"status": "not_found", "error": str(e)}

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

    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态详情

        Args:
            task_id: 任务ID

        Returns:
            Dict: 包含任务详细信息的字典，如果任务不存在返回 {"status": "not_found"}
        """
        try:
            # 从数据库获取任务信息
            try:
                task = ModelTask.get(ModelTask.task_id == task_id)
            except DoesNotExist:
                logger.warning("任务不存在: %s", task_id)
                return {"status": "not_found"}

            # 获取最新进度
            progress = self._progress_cache.get(task_id, task.progress)

            return {
                "status": task.status,
                "progress": progress,
                "result": task.result,
                "error": task.error,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "input_params": json.loads(task.input_params),
            }
        except (DatabaseError, IntegrityError, TypeError, ValueError) as e:
            logger.error("获取任务状态失败: %s", str(e))
            return {"status": "error", "message": str(e)}
