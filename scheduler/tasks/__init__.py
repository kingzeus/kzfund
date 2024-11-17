from .data_sync import DataSyncTask
from .fund_detail import FundDetailTask
from .fund_info import FundInfoTask
from .portfolio import PortfolioUpdateTask
from .task_factory import TaskFactory


class TaskStatus:
    """任务状态常量"""

    PENDING = "pending"  # 等待执行
    RUNNING = "running"  # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"  # 执行失败
    PAUSED = "paused"  # 已暂停


def init_tasks():
    """初始化任务类型"""
    factory = TaskFactory()  # 获取单例实例

    factory.register(DataSyncTask)
    # factory.register(PortfolioUpdateTask)
    factory.register(FundInfoTask)
    factory.register(FundDetailTask)


__all__ = ["TaskFactory", "TaskStatus", "init_tasks"]
