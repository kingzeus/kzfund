from kz_dash.scheduler.task_factory import TaskFactory
from task.fund_nav import FundNavTask
from task.sync_fund_nav import SyncFundNavTask
from task.sync_fund_page import SyncFundListPageTask
from task.data_sync import DataSyncTask
from task.fund_detail import FundDetailTask
from task.fund_info import FundInfoTask


def init_tasks():
    """初始化任务类型"""
    factory = TaskFactory()  # 获取单例实例

    factory.register(DataSyncTask)
    # factory.register(PortfolioUpdateTask)
    factory.register(FundInfoTask)
    factory.register(FundDetailTask)
    factory.register(FundNavTask)
    factory.register(SyncFundNavTask)  # 同步基金净值
    factory.register(SyncFundListPageTask)  # 同步基金净值列表页面
