import time
from dash import html, dcc, callback, Output, Input, State, MATCH, no_update
import feffery_antd_components as fac
import uuid

from data_source.proxy import DataSourceProxy


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
        print(select_props)
        super().__init__([fac.AntdSelect(id=self.ids.select(aio_id), **select_props)])

    @callback(
        Output(ids.select(MATCH), "options"),
        State("store-local-data-source", "data"),
        Input(ids.select(MATCH), "debounceSearchValue"),
    )
    def update_options(data_source, debounceSearchValue):
        if not debounceSearchValue:
            return no_update

        try:
            return DataSourceProxy(data_source).get_quick_tips(debounceSearchValue)
        except Exception as e:
            print(f"获取基金代码失败: {e}")
            return []
