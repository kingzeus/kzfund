from data_source.factory import DataSourceFactory
from data_source.implementations.eastmoney import EastMoneyDataSource
from data_source.implementations.simple import SimpleDataSource


def init_data_source():
    """初始化数据源"""

    DataSourceFactory.register(SimpleDataSource)
    DataSourceFactory.register(EastMoneyDataSource)
