"""删除确认弹窗模块

提供交易记录删除确认功能:
- 渲染删除确认弹窗
- 处理删除操作
"""

import dash
import feffery_antd_components as fac
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from kz_dash.models.database import delete_record
from models.database import get_transactions
from models.fund_user import ModelFundTransaction


def render_delete_confirm_modal() -> fac.AntdModal:
    """渲染删除确认弹窗"""
    return fac.AntdModal(
        id="transaction-delete-confirm-modal",
        title="确认删除",
        visible=False,
        children="确定要删除这条交易记录吗？删除后无法恢复。",
        okText="确定",
        cancelText="取消",
        renderFooter=True,
        maskClosable=False,
    )


@callback(
    [
        Output("transaction-store", "data", allow_duplicate=True),
        Output("transaction-delete-confirm-modal", "visible", allow_duplicate=True),
    ],
    Input("transaction-delete-confirm-modal", "okCounts"),
    State("editing-transaction-id", "data"),
    prevent_initial_call=True,
)
def handle_delete_confirm(ok_counts, transaction_id):
    """处理删除确操作"""
    if not ok_counts or not transaction_id:
        raise PreventUpdate

    if delete_record(ModelFundTransaction, {"id": transaction_id}):
        return get_transactions(), False
    return dash.no_update, False
