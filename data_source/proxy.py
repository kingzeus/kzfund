import logging
from typing import Optional, Dict, Any, Callable, TypeVar
from datetime import datetime

from config import DATA_SOURCE_DEFAULT
from utils.response import response
from .data_source_factory import DataSourceFactory


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
            logger.debug(f"初始化数据源: {data_source_name}")
        except Exception as e:
            logger.error(f"初始化数据源失败: {str(e)}", exc_info=True)
            raise Exception(f"初始化数据源失败: {str(e)}")

    def _call_api(
        self,
        func_name: str,
        api_func: Callable[..., T],
        error_msg: str,
        return_empty: bool = False,
        is_array: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """通用API调用方法

        Args:
            func_name: API函数名称，用于日志
            api_func: 要调用的API函数
            error_msg: 错误信息模板
            return_empty: 出错时是否返回空值而不是抛出异常
            is_array: 返回值是否为数组类型
            args: 传递给API函数的位置参数
            kwargs: 传递给API函数的关键字参数

        Returns:
            统一格式的API响应
        """
        if not self._data_source:
            logger.error("数据源未初始化")
            return response(message="数据源未初始化", code=500, is_array=is_array)

        try:
            logger.debug(f"调用{func_name}: {kwargs}")
            result = api_func(*args, **kwargs)
            return response(data=result, message="success", is_array=is_array)
        except Exception as e:
            logger.error(f"{error_msg}: {str(e)}", exc_info=True)
            if return_empty:
                return response(message=str(e), code=200, is_array=is_array)
            return response(message=str(e), code=500, is_array=is_array)

    def get_quick_tips(self, search_text: str) -> Dict[str, Any]:
        """获取基金代码快速提示"""
        return self._call_api(
            "get_quick_tips",
            self._data_source.get_quick_tips,
            "获取基金代码失败",
            return_empty=True,
            is_array=True,
            search_text=search_text,
        )

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """获取基金信息"""
        return self._call_api(
            "get_fund_info",
            self._data_source.get_fund_info,
            "获取基金信息失败",
            is_array=False,
            fund_code=fund_code,
        )

    def get_fund_detail(self, fund_code: str) -> Dict[str, Any]:
        """获取基金详情"""
        return self._call_api(
            "get_fund_detail",
            self._data_source.get_fund_detail,
            "获取基金详情失败",
            is_array=False,
            fund_code=fund_code,
        )

    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取基金历史净值"""
        return self._call_api(
            "get_fund_nav_history",
            self._data_source.get_fund_nav_history,
            "获取基金历史净值失败",
            is_array=True,
            fund_code=fund_code,
            start_date=start_date,
            end_date=end_date,
        )
