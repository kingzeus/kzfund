from .fund_detail import FundDetailTask
from .example import ExampleTask
from .data_sync import DataSyncTask
from .fund_info import FundInfoTask
from .task_factory import TaskFactory


def init_tasks():
    """初始化任务类型"""
    factory = TaskFactory()  # 获取单例实例
    factory.register(ExampleTask)
    factory.register(DataSyncTask)
    # factory.register(PortfolioUpdateTask)
    factory.register(FundInfoTask)
    factory.register(FundDetailTask)
