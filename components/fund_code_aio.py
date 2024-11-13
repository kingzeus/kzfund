import time
from dash import html, dcc, callback, Output, Input, State, MATCH, no_update
import feffery_antd_components as fac
import uuid
import logging

from config import DATA_SOURCE_DEFAULT
from data_source.proxy import DataSourceProxy


logger = logging.getLogger(__name__)


class FundCodeAIO(html.Div):
    class ids:
        select = lambda aio_id: {
            "component": "FundCodeAIO",
            "subcomponent": "select",
            "aio_id": aio_id,
        }

    ids = ids

    def __init__(
        self,
        aio_id=None,
        placeholder: str = None,
        debounceWait: int = None,
    ):
        if aio_id is None:
            aio_id = str(uuid.uuid4())

        select_props = {}
        select_props["placeholder"] = placeholder or "请输入基金代码"
        select_props["debounceWait"] = debounceWait or 200
        select_props["options"] = []
        select_props["optionFilterMode"] = "remote-match"
        select_props["style"] = {"width": "100%"}

        logger.debug(f"初始化基金代码选择器: {select_props}")
        super().__init__([fac.AntdSelect(id=self.ids.select(aio_id), **select_props)])

    @callback(
        Output(ids.select(MATCH), "options"),
        Input(ids.select(MATCH), "debounceSearchValue"),
    )
    def update_options(debounceSearchValue):
        if not debounceSearchValue:
            return no_update

        try:
            logger.debug(f"获取基金代码提示: {debounceSearchValue}")
            response = DataSourceProxy(DATA_SOURCE_DEFAULT).get_quick_tips(
                debounceSearchValue
            )

            # 检查响应状态
            if response["code"] != 200:
                logger.error(f"获取基金代码失败: {response['message']}")
                return []

            # 从响应中提取数据
            options = response["data"]
            logger.debug(f"获取到 {len(options)} 个提示选项")
            return options

        except Exception as e:
            logger.error(f"获取基金代码失败: {str(e)}", exc_info=True)
            return []
