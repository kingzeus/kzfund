from data_source.data_source_factory import DataSourceFactory
from data_source.implementations.eastmoney import EastMoneyDataSource


def init_data_source():
    """初始化数据源"""

    DataSourceFactory.register(EastMoneyDataSource)
