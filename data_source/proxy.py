import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from config import DATA_SOURCE_DEFAULT
from .interface import IDataSource
from .factory import DataSourceFactory


logger = logging.getLogger(__name__)


class DataSourceProxy:
    """数据源代理"""

    def __init__(self, data_source_name: Optional[str] = None):
        """
        初始化数据源代理
        :param data_source_name: 数据源名称
        """
        if not data_source_name:
            data_source_name = DATA_SOURCE_DEFAULT

        try:
            self._data_source = DataSourceFactory.create(data_source_name)
            logger.debug(f"初始化数据源: {data_source_name}")
        except Exception as e:
            logger.error(f"初始化数据源失败: {str(e)}", exc_info=True)
            raise Exception(f"初始化数据源失败: {str(e)}")

    def get_quick_tips(self, search_text: str) -> List[Dict[str, str]]:
        """获取基金代码快速提示"""
        if not self._data_source:
            logger.error("数据源未初始化")
            raise Exception("数据源未初始化")

        try:
            logger.debug(f"获取基金代码提示: {search_text}")
            return self._data_source.get_quick_tips(search_text)
        except Exception as e:
            logger.error(f"获取基金代码失败: {str(e)}", exc_info=True)
            return []

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """获取基金信息"""
        if not self._data_source:
            logger.error("数据源未初始化")
            raise Exception("数据源未初始化")

        try:
            logger.debug(f"获取基金信息: {fund_code}")
            return self._data_source.get_fund_info(fund_code)
        except Exception as e:
            logger.error(f"获取基金信息失败: {str(e)}", exc_info=True)
            raise Exception(f"获取基金信息失败: {str(e)}")

    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        if not self._data_source:
            logger.error("数据源未初始化")
            raise Exception("数据源未初始化")

        try:
            logger.debug(
                f"获取基金历史净值: {fund_code}, "
                f"开始日期: {start_date}, "
                f"结束日期: {end_date}"
            )
            return self._data_source.get_fund_nav_history(
                fund_code, start_date, end_date
            )
        except Exception as e:
            logger.error(f"获取基金历史净值失败: {str(e)}", exc_info=True)
            raise Exception(f"获取基金历史净值失败: {str(e)}")
