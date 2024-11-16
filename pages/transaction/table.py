"""交易记录表格模块

提供交易记录的表格展示功能:
- 表格数据展示
- 表格操作按钮
"""

from typing import Any, Dict, List

import dash
import feffery_antd_components as fac
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from components.fund_code_aio import FundCodeAIO
from models.database import get_portfolio

from .utils import build_cascader_options

# 表格样式常量
TABLE_STYLES = {"marginTop": "8px", "width": "100%"}


def render_transaction_table(initial_data: List[Dict[str, Any]]) -> fac.AntdCard:
    """渲染交易记录表格

    Args:
        initial_data: 初始交易数据列表

    Returns:
        包含表格的卡片组件
    """
    return fac.AntdCard(
        title="交易记录",
        bordered=False,
        extra=[
            fac.AntdButton(
                "手工输入",
                type="primary",
                icon=fac.AntdIcon(icon="antd-plus"),
                id="add-transaction-btn",
            ),
        ],
        children=[
            fac.AntdTable(
                id="transaction-list",
                columns=[
                    {
                        "title": "交易ID",
                        "dataIndex": "id",
                        "key": "id",
                        "width": "15%",
                        "renderOptions": {"renderType": "copyable"},
                    },
                    {
                        "title": "组合",
                        "dataIndex": "portfolio_name",
                        "key": "portfolio_name",
                        "width": "10%",
                    },
                    {
                        "title": "基金代码",
                        "dataIndex": "fund_code",
                        "key": "fund_code",
                        "width": "10%",
                    },
                    {
                        "title": "基金名称",
                        "dataIndex": "fund_name",
                        "key": "fund_name",
                        "width": "15%",
                    },
                    {
                        "title": "交易金额",
                        "dataIndex": "amount",
                        "key": "amount",
                        "width": "10%",
                    },
                    {
                        "title": "交易时间",
                        "dataIndex": "trade_time",
                        "key": "trade_time",
                        "width": "15%",
                    },
                    {
                        "title": "操作",
                        "dataIndex": "operation",
                        "key": "operation",
                        "width": "15%",
                        "renderOptions": {
                            "renderType": "button",
                        },
                    },
                ],
                data=initial_data,
                bordered=True,
                size="small",
                pagination={
                    "pageSize": 10,
                    "showSizeChanger": True,
                    "showQuickJumper": True,
                },
                style=TABLE_STYLES,
            ),
        ],
        bodyStyle={"padding": "12px"},
        style={"width": "100%"},
    )


@callback(
    Output("transaction-list", "data"),
    Input("transaction-store", "data"),
    prevent_initial_call=True,
)
def update_transaction_table(store_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Store数据更新时，更新交易记录表格"""
    return store_data


@callback(
    [
        Output("transaction-modal", "visible", allow_duplicate=True),
        Output("transaction-modal", "title"),
        Output("portfolio-cascader", "options"),
        Output("portfolio-cascader", "value"),
        Output(FundCodeAIO.ids.select("fund-code-aio"), "value"),
        Output("transaction-type-select", "value"),
        Output("amount-input", "value"),
        Output("trade-time-picker", "value"),
        Output("transaction-delete-confirm-modal", "visible"),
        Output("editing-transaction-id", "data"),
    ],
    Input("transaction-list", "nClicksButton"),
    State("transaction-list", "clickedCustom"),
    State("transaction-store", "data"),
    prevent_initial_call=True,
)
def handle_button_click(nClicksButton, custom_info, store_data):
    """处理表格按钮点击事件

    Args:
        nClicksButton: 按钮点击次数
        custom_info: 按钮自定义数据
        store_data: 当前表格数据

    Returns:
        tuple: 包含所有表单项的值
    """
    if not nClicksButton or not custom_info:
        raise PreventUpdate

    action = custom_info.get("action")
    transaction_id = custom_info.get("id")
    transaction = next((t for t in store_data if t["id"] == transaction_id), None)

    if not transaction:
        raise PreventUpdate

    if action == "edit":
        # 找到当前交易记录对应的组合路径
        portfolio_id = transaction["portfolio_id"]
        # 从组合信息中获取账户ID
        portfolio = get_portfolio(portfolio_id)
        if not portfolio:
            raise PreventUpdate

        account_id = portfolio["account_id"]
        cascader_value = [account_id, portfolio_id]

        return (
            True,  # modal visible
            "编辑交易记录",  # modal title
            build_cascader_options(),  # cascader options
            cascader_value,  # cascader value
            transaction["fund_code"],  # fund code
            transaction["type"],  # transaction type
            float(transaction["amount"].replace("¥", "").replace(",", "")),  # amount
            transaction["trade_time"],  # trade time
            False,  # delete modal visible
            transaction_id,  # editing id
        )
    elif action == "delete":
        return (
            False,  # modal visible
            dash.no_update,  # modal title
            [],  # cascader options
            None,  # cascader value
            "",  # fund code
            None,  # transaction type
            None,  # amount
            None,  # trade time
            True,  # delete modal visible
            transaction_id,  # editing id
        )

    return dash.no_update
