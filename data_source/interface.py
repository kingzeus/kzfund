"""
数据源接口定义模块。
定义了数据源的抽象基类和通用接口。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional


class IDataSource(ABC):
    """数据源接口基类"""

    @abstractmethod
    def get_quick_tips(self, search_text: str) -> List[Dict[str, str]]:
        """
        获取快速提示，可以参考 https://fac.feffery.tech/AntdSelect 的 options 属性
        Args:
            search_text: 搜索文本
        Returns:
            List[Dict]: [{"label": "基金名称", "value": "基金代码"}]
        """

    @abstractmethod
    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """
        获取基金详细信息
        Args:
            fund_code: 基金代码
        Returns:
            Dict: {
                "code": "基金代码",
                "name": "基金名称",
                "type": "基金类型",
                "company": "基金公司",
                "nav": "最新净值",
                "nav_date": "净值日期",
                "description": "基金描述"
            }
        """

    @abstractmethod
    def get_fund_detail(self, fund_code: str) -> Dict[str, Any]:
        """
        获取基金详细信息
        Args:
            fund_code: 基金代码
        Returns:
            Dict: {
                "code": "基金代码",
                "name": "基金名称",
            }
        """

    @abstractmethod
    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取基金历史净值
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
        Returns:
            List[Dict]: [{
                "date": "日期",
                "nav": "单位净值",
                "acc_nav": "累计净值",
                "daily_return": "日收益率"
            }]
        """

    @classmethod
    @abstractmethod
    def get_version(cls) -> str:
        """数据源接口版本"""

    @classmethod
    @abstractmethod
    def get_name(cls) -> str:
        """数据源名称"""
