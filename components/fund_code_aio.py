import logging
import uuid
from typing import Any, Dict, List

import feffery_antd_components as fac
from dash import MATCH, Input, Output, callback, html, no_update
from requests.exceptions import RequestException

from config import DATA_SOURCE_DEFAULT
from data_source.proxy import DataSourceProxy

logger = logging.getLogger(__name__)


class FundCodeAIO(html.Div):
    class ids:
        @staticmethod
        def select(aio_id: str) -> Dict[str, str]:
            return {
                "component": "FundCodeAIO",
                "subcomponent": "select",
                "aio_id": aio_id,
            }

    ids = ids

    def __init__(
        self,
        aio_id: str = None,
        placeholder: str = None,
        debounce_wait: int = None,
    ):
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        select_props = {
            "placeholder": placeholder or "请输入基金代码",
            "debounceWait": debounce_wait or 200,
            "options": [],
            "optionFilterMode": "remote-match",
            "style": {"width": "100%"},
        }

        logger.debug("初始化基金代码选择器: %s", select_props)
        super().__init__([fac.AntdSelect(id=self.ids.select(aio_id), **select_props)])

    @staticmethod
    @callback(
        Output(ids.select(MATCH), "options"),
        Input(ids.select(MATCH), "debounce_search_value"),
    )
    def update_options(debounce_search_value: str) -> List[Dict[str, Any]]:
        if not debounce_search_value:
            return no_update

        try:
            logger.debug("获取基金代码提示: %s", debounce_search_value)
            response = DataSourceProxy(DATA_SOURCE_DEFAULT).get_quick_tips(debounce_search_value)

            # 检查响应状态
            if response["code"] != 200:
                logger.error("获取基金代码失败: %s", response["message"])
                return []

            # 从响应中提取数据
            options = response["data"]
            logger.debug("获取到 %d 个提示选项", len(options))
            return options

        except RequestException as e:
            logger.error("获取基金代码失败: %s", str(e), exc_info=True)
            return []
        except (KeyError, ValueError) as e:
            logger.error("解析基金代码数据失败: %s", str(e), exc_info=True)
            return []
