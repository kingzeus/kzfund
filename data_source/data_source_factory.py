from typing import Dict, Type
import logging
from .interface import IDataSource


logger = logging.getLogger(__name__)


class DataSourceFactory:
    """数据源工厂"""

    _sources: Dict[str, Type[IDataSource]] = {}

    @classmethod
    def register(cls, source_class: Type[IDataSource]) -> None:
        """注册新的数据源类型"""
        logger.info(
            "注册数据源: %s %s", source_class.get_name(), source_class.get_version()
        )
        cls._sources[source_class.get_name()] = source_class

    @classmethod
    def create(cls, name: str) -> IDataSource:
        """创建数据源实例"""
        if name not in cls._sources:
            error_msg = f"未知的数据源类型: {name}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug("创建数据源实例: %s", name)
        return cls._sources[name]()

    @classmethod
    def get_available_sources(cls) -> Dict[str, Type[IDataSource]]:
        """获取所有可用的数据源类型"""
        logger.debug("获取可用数据源列表")
        return cls._sources.copy()
