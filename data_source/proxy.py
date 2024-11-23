import logging
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar, Union

from config import DATA_SOURCE_DEFAULT
from data_source import DataSourceFactory
from utils.response import format_response

logger = logging.getLogger(__name__)
T = TypeVar("T")  # 用于泛型返回类型


class DataSourceProxy:
    """数据源代理"""

    def __init__(self, data_source_name: Optional[str] = None):
        """初始化数据源代理"""
        if not data_source_name:
            data_source_name = DATA_SOURCE_DEFAULT

        try:
            self._data_source = DataSourceFactory.create(data_source_name)
            logger.info("数据源 %s 初始化成功", data_source_name)
        except ValueError as e:
            logger.error("初始化数据源失败: %s", str(e))
            raise ValueError(f"初始化数据源失败: {str(e)}") from e

    def _call_api(
        self,
        func_name: str,
        api_func: Callable[..., T],
        error_msg: str,
        *args: Any,
        return_empty: bool = False,
        is_array: bool = True,
        **kwargs: Any,
    ) -> Dict[str, Union[T, str, int, bool]]:
        """通用API调用方法

        Args:
            func_name: API函数名称，用于日志
            api_func: 要调用的API函数
            error_msg: 错误信息模板
            args: 传递给API函数的位置参数
            return_empty: 出错时是否返回空值而不是抛出异常
            is_array: 返回值是否为数组类型
            kwargs: 传递给API函数的关键字参数

        Returns:
            统一格式的API响应
        """
        if not self._data_source:
            logger.error("数据源未初始化")
            return format_response(message="数据源未初始化", code=500, is_array=is_array)

        try:
            logger.debug("调用%s: %s", func_name, str(kwargs))
            result = api_func(*args, **kwargs)
            return format_response(data=result, message="success", is_array=is_array)
        except ValueError as e:
            logger.error("%s: %s", error_msg, str(e))
            if return_empty:
                return format_response(message=str(e), code=200, is_array=is_array)
            return format_response(message=str(e), code=500, is_array=is_array)

    def get_quick_tips(self, search_text: str) -> Dict[str, Any]:
        """获取基金代码快速提示"""
        return self._call_api(
            func_name="get_quick_tips",
            api_func=self._data_source.get_quick_tips,
            error_msg="获取基金代码失败",
            search_text=search_text,
            return_empty=True,
            is_array=True,
        )

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """获取基金信息"""
        return self._call_api(
            func_name="get_fund_info",
            api_func=self._data_source.get_fund_info,
            error_msg="获取基金信息失败",
            fund_code=fund_code,
            is_array=False,
        )

    def get_fund_detail(self, fund_code: str) -> Dict[str, Any]:
        """获取基金详情"""
        return self._call_api(
            func_name="get_fund_detail",
            api_func=self._data_source.get_fund_detail,
            error_msg="获取基金详情失败",
            fund_code=fund_code,
            is_array=False,
        )

    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """获取基金历史净值"""
        return self._call_api(
            func_name="get_fund_nav_history",
            api_func=self._data_source.get_fund_nav_history,
            error_msg="获取基金历史净值失败",
            fund_code=fund_code,
            start_date=start_date,
            end_date=end_date,
            is_array=True,
        )

    def get_fund_nav_history_size(
        self,
    ) -> Dict[str, Any]:
        """获取基金历史净值"""
        return self._call_api(
            func_name="get_fund_nav_history_size",
            api_func=self._data_source.get_fund_nav_history_size,
            error_msg="获取基金历史净值失败",
        )
