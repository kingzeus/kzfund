from scheduler.tasks.fund_nav import FundNavTask
from scheduler.tasks.sync_fund_nav import SyncFundNavTask

from .data_sync import DataSyncTask
from .fund_detail import FundDetailTask
from .fund_info import FundInfoTask
from .task_factory import TaskFactory


class TaskStatus:
    """任务状态常量"""

    PENDING = "等待中"  # 等待执行
    RUNNING = "运行中"  # 正在执行
    COMPLETED = "已完成"  # 执行完成
    FAILED = "失败"  # 执行失败
    TIMEOUT = "超时"  # 超时
    PAUSED = "已暂停"  # 已暂停


def init_tasks():
    """初始化任务类型"""
    factory = TaskFactory()  # 获取单例实例

    factory.register(DataSyncTask)
    # factory.register(PortfolioUpdateTask)
    factory.register(FundInfoTask)
    factory.register(FundDetailTask)
    factory.register(FundNavTask)
    factory.register(SyncFundNavTask)  # 同步基金净值


__all__ = ["TaskFactory", "TaskStatus", "init_tasks"]
