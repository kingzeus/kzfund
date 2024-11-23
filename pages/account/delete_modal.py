import dash
import feffery_antd_components as fac
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from models.account import ModelPortfolio, delete_account
from models.database import delete_record
from pages.account.table import get_account_table_data


def render_delete_confirm_modal() -> fac.AntdModal:
    """渲染删除确认弹窗

    提供通用的删除确认功能:
    - 支持账户删除确认
    - 支持组合删除确认
    - 统一的删除处理逻辑

    Returns:
        AntdModal: 删除确认弹窗组件
        - 显示删除警告信息
        - 确认和取消按钮
    """
    return fac.AntdModal(
        id="account-delete-confirm-modal",
        title="确认删除",
        visible=False,
        children="确定要删除吗？删除后无法恢复。",
        okText="确定",
        cancelText="取消",
        renderFooter=True,
        maskClosable=False,
    )


@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("account-delete-confirm-modal", "visible", allow_duplicate=True),
    ],
    Input("account-delete-confirm-modal", "okCounts"),
    [
        State("editing-account-id", "data"),
        State("account-list", "clickedCustom"),
    ],
    prevent_initial_call=True,
)
def handle_delete_confirm(ok_counts, object_id, custom_info):
    """处理删除确认操作

    Args:
        ok_counts: 确认按钮点击次数
        object_id: 要删除的对象ID
        custom_info: 包含对象类型信息的自定义数据

    Returns:
        tuple: (更新后的数据, 弹窗可见性)
    """
    if not ok_counts or not object_id:
        raise PreventUpdate

    success = False
    if custom_info and custom_info.get("type") == "portfolio":
        success = delete_record(ModelPortfolio, {"id": object_id})
    else:
        success = delete_account(object_id)

    if success:
        return get_account_table_data(), False
    return dash.no_update, False
