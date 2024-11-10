from .example import ExampleTask
from .data_sync import DataSyncTask
from .portfolio import PortfolioUpdateTask
from .fund_info import FundInfoTask
from .base import BaseTask
from .factory import TaskFactory


def init_tasks():
    """初始化任务类型"""
    factory = TaskFactory()  # 获取单例实例
    factory.register(ExampleTask)
    factory.register(DataSyncTask)
    # factory.register(PortfolioUpdateTask)
    factory.register(FundInfoTask)
