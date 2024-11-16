import logging
import uuid
from datetime import datetime
from typing import Dict, List

from flask_apscheduler import APScheduler

from config import SCHEDULER_CONFIG
from models.task import TaskHistory
from scheduler.tasks import TaskFactory
from utils.singleton import Singleton

# 创建调度器实例
scheduler = APScheduler()
logger = logging.getLogger(__name__)


class TaskStatus:
    """任务状态常量"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"  # 执行失败
    PAUSED = "paused"  # 已暂停


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

    def _create_job_id(self) -> str:
        """生成UUID格式的任务ID"""
        return str(uuid.uuid4())

    def _task_wrapper(self, task_type: str, task_id: str, **kwargs):
        """任务执行包装器

        职责:
        1. 更新任务执行状态
        2. 捕获和记录任务异常
        3. 同步任务最终进度到数据库
        """
        try:
            # 更新任务状态为运行中
            task_history = TaskHistory.get(TaskHistory.task_id == task_id)
            task_history.status = TaskStatus.RUNNING
            task_history.start_time = datetime.now()
            task_history.save()
            logger.info("开始执行任务: %s (ID: %s)", task_type, task_id)

            # 执行具体任务
            result = TaskFactory().execute_task(task_type, task_id, **kwargs)

            # 任务成功完成
            task_history.status = TaskStatus.COMPLETED
            task_history.result = str(result)
            logger.info("任务执行完成: %s (ID: %s)", task_type, task_id)

        except Exception as e:
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
            except Exception as e:
                logger.error("保存任务最终状态失败: %s", str(e))

    def add_task(self, task_type: str, **kwargs) -> str:
        """添加新任务

        Args:
            task_type: 任务类型
            **kwargs: 任务参数(包含 priority、timeout 等)

        Returns:
            task_id: 新创建的任务ID

        Raises:
            ValueError: 任务参数验证失败
        """
        # ���证任务参数
        is_valid, error_message = TaskFactory().validate_task_params(task_type, kwargs)
        if not is_valid:
            logger.error("任务参数验证失败: %s", error_message)
            raise ValueError(error_message)

        task_id = self._create_job_id()
        task_config = TaskFactory().get_task_types().get(task_type, {})

        # 创建任务历史记录
        TaskHistory.create(
            task_id=task_id,
            name=task_config.get("name", task_type),
            priority=kwargs.get("priority", task_config.get("priority", 0)),
            status=TaskStatus.PENDING,
            timeout=kwargs.get(
                "timeout",
                task_config.get("timeout", SCHEDULER_CONFIG["DEFAULT_TIMEOUT"]),
            ),
        )

        # 添加到调度器立即执行
        self.scheduler.add_job(
            func=self._task_wrapper,
            args=(task_type, task_id),
            kwargs=kwargs,
            id=task_id,
            name=task_config.get("name", task_type),
            trigger="date",
            misfire_grace_time=SCHEDULER_CONFIG["SCHEDULER_JOB_DEFAULTS"]["misfire_grace_time"],
        )

        return task_id

    def pause_task(self, task_id: str) -> bool:
        """暂停指定任务"""
        try:
            self.scheduler.pause_job(task_id)
            TaskHistory.update(status=TaskStatus.PAUSED).where(
                TaskHistory.task_id == task_id
            ).execute()
            logger.info("任务已暂停: %s", task_id)
            return True
        except Exception as e:
            logger.error("暂停任务失败: %s:%s", task_id, str(e), exc_info=True)
            return False

    def resume_task(self, task_id: str) -> bool:
        """恢复已暂停的任务"""
        try:
            self.scheduler.resume_job(task_id)
            TaskHistory.update(status=TaskStatus.PENDING).where(
                TaskHistory.task_id == task_id
            ).execute()
            logger.info("任务已恢复: %s", task_id)
            return True
        except Exception as e:
            logger.error("恢复任务失败: %s: %s", task_id, str(e), exc_info=True)
            return False

    def get_task_history(self, limit: int = 100) -> List[TaskHistory]:
        """获取最近的任务历史记录

        Args:
            limit: 返回的最大记录数,默认100条

        Returns:
            任务历史记录列表,每条记录为TaskHistory实例
        """
        try:
            query = TaskHistory.select().order_by(TaskHistory.created_at.desc()).limit(limit)

            return list(query)
        except Exception as e:
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
                query = TaskHistory.select(TaskHistory.task_id, TaskHistory.progress).where(
                    TaskHistory.task_id.in_(missing_task_ids)
                )
                progress_dict.update({task.task_id: task.progress for task in query})
            except Exception as e:
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
            task = TaskHistory.get_or_none(TaskHistory.task_id == task_id)

            if not task:
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
                "priority": task.priority,
                "status": current_status,
                "progress": progress,
                "result": task.result,
                "error": task.error,
                "start_time": task.start_time,
                "end_time": task.end_time,
                "timeout": task.timeout,
                "created_at": task.created_at,
            }

        except Exception as e:
            logger.error("获取任务信息失败: %s, 错误: %s", task_id, str(e), exc_info=True)
            return {"status": "not_found", "error": str(e)}
