from typing import Callable, Dict, Any, List
from datetime import datetime
import uuid
from flask_apscheduler import APScheduler
from models.task import TaskHistory
from config import SCHEDULER_CONFIG
from utils.singleton import Singleton
from scheduler.tasks import TaskFactory

# 创建调度器实例
scheduler = APScheduler()

# ============= 常量定义 =============
class TaskStatus:
    """任务状态常量"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"  # 执行失败
    PAUSED = "paused"  # 已暂停


# ============= 任务管理器 =============
@Singleton
class JobManager:
    """任务管理器

    负责:
    1. 任务的添加、暂停、恢复
    2. 任务状态的跟踪和更新
    3. 任务历史记录的管理
    """

    def __init__(self):
        """初始化任务管理器"""
        self.scheduler = scheduler

    def init_app(self, app):
        """初始化 Flask 应用

        Args:
            app: Flask应用实例
        """

        # 配置调度器
        app.config.update(SCHEDULER_CONFIG)
        self.scheduler.init_app(app)
        self.scheduler.start()

    def _create_job_id(self) -> str:
        """生成任务ID

        Returns:
            UUID格式的任务ID
        """
        return str(uuid.uuid4())

    def _task_wrapper(self, task_type: str, task_id: str, **kwargs):
        """任务包装器,用于跟踪任务状态

        Args:
            task_type: 任务类型
            task_id: 任务ID
            **kwargs: 任务参数

        Raises:
            Exception: 任务执行过程中的异常
        """
        try:
            # 更新任务状态为运行中
            task_history = TaskHistory.get(TaskHistory.task_id == task_id)
            task_history.status = TaskStatus.RUNNING
            task_history.start_time = datetime.now()
            task_history.save()

            # 执行任务
            result = TaskFactory().execute_task(task_type, task_id, **kwargs)

            # 更新任务状态为完成
            task_history.status = TaskStatus.COMPLETED
            task_history.result = str(result)
            task_history.progress = 100

        except Exception as e:
            # 更新任务状态为失败
            task_history.status = TaskStatus.FAILED
            task_history.error = str(e)
            raise
        finally:
            task_history.end_time = datetime.now()
            task_history.save()

    def add_task(self, task_type: str, **kwargs) -> str:
        """添加任务

        Args:
            task_type: 任务类型
            **kwargs: 任务参数,包括:
                - priority: 优先级(可选)
                - timeout: 超时时间(可选)
                - 其他: 任务自定义参数

        Returns:
            任务ID

        Raises:
            ValueError: 当必需参数缺失时
        """
        # 验证任务参数

        if task_type == "fund_info" and "fund_code" not in kwargs:
            raise ValueError("fund_info任务需要提供fund_code参数")

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

        # 添加任务到调度器
        self.scheduler.add_job(
            func=self._task_wrapper,
            args=(task_type, task_id),
            kwargs=kwargs,
            id=task_id,
            name=task_config.get("name", task_type),
            trigger="date",  # 立即执行一次
            misfire_grace_time=SCHEDULER_CONFIG["SCHEDULER_JOB_DEFAULTS"][
                "misfire_grace_time"
            ],
        )

        return task_id

    def pause_task(self, task_id: str) -> bool:
        """暂停任务

        Args:
            task_id: 任务ID

        Returns:
            操作是否成功
        """
        try:
            self.scheduler.pause_job(task_id)
            TaskHistory.update(status=TaskStatus.PAUSED).where(
                TaskHistory.task_id == task_id
            ).execute()
            return True
        except Exception as e:
            print(f"暂停任务失败: {e}")  # 添加错误日志
            return False

    def resume_task(self, task_id: str) -> bool:
        """恢复任务

        Args:
            task_id: 任务ID

        Returns:
            操作是否成功
        """
        try:
            self.scheduler.resume_job(task_id)
            TaskHistory.update(status=TaskStatus.PENDING).where(
                TaskHistory.task_id == task_id
            ).execute()
            return True
        except Exception as e:
            print(f"恢复任务失败: {e}")  # 添加错误日志
            return False

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态信息字典
        """
        try:
            task_history = TaskHistory.get(TaskHistory.task_id == task_id)
            return task_history.to_dict()
        except TaskHistory.DoesNotExist:
            return {"status": "not_found"}

    def get_task_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务历史

        Args:
            limit: 返回记录数量限制

        Returns:
            任务历史记录列表
        """
        query = (
            TaskHistory.select().order_by(TaskHistory.created_at.desc()).limit(limit)
        )
        return [task.to_dict() for task in query]

    def get_running_tasks(self) -> List[Dict[str, Any]]:
        """获取正在运行的任务

        Returns:
            运行中的任务列表
        """
        query = TaskHistory.select().where(TaskHistory.status == TaskStatus.RUNNING)
        return [task.to_dict() for task in query]

    def get_failed_tasks(self) -> List[Dict[str, Any]]:
        """获取失败的任务

        Returns:
            失败的任务列表
        """
        query = TaskHistory.select().where(TaskHistory.status == TaskStatus.FAILED)
        return [task.to_dict() for task in query]
