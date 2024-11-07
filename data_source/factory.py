from typing import Dict, Type
from .interface import IDataSource


class DataSourceFactory:
    """数据源工厂"""

    _sources: Dict[str, Type[IDataSource]] = {}

    @classmethod
    def register(cls, source_class: Type[IDataSource]) -> None:
        """注册新的数据源类型"""
        print(f"注册数据源: {source_class.get_name()} {source_class.get_version()}")
        cls._sources[source_class.get_name()] = source_class

    @classmethod
    def create(cls, name: str) -> IDataSource:
        """创建数据源实例"""
        if name not in cls._sources:
            raise ValueError(f"未知的数据源类型: {name}")

        return cls._sources[name]()

    @classmethod
    def get_available_sources(cls) -> Dict[str, Type[IDataSource]]:
        """获取所有可用的数据源类型"""
        return cls._sources.copy()
