from typing import List, Dict, Any
import feffery_antd_components as fac
from dash import callback, Input, Output, State
from dash.exceptions import PreventUpdate
import dash
from models.database import get_accounts, get_portfolios, get_portfolio
from utils.datetime import format_datetime
from .utils import create_operation_buttons


"""账户表格模块

提供账户和组合数据的表格展示功能:
- 嵌套表格显示账户和组合的层级关系
- 表格数据的获取和转换
- 表格的操作按钮和交互处理
"""


def get_account_table_data() -> List[Dict[str, Any]]:
    """获取并格式化账户表格数据

    Returns:
        List[Dict[str, Any]]: 格式化后的账户数据列表
        - 包含账户基本信息
        - 包含嵌套的组合数据
        - 包含操作按钮配置
    """
    accounts = get_accounts()
    table_data = []

    for account in accounts:
        portfolios = get_portfolios(account["id"])
        portfolio_data = []

        for p in portfolios:
            operation_buttons = []
            if not p["is_default"]:
                operation_buttons = create_operation_buttons(
                    p["id"], "portfolio", account["id"], is_danger=True
                )

            portfolio_data.append(
                {
                    "key": p["id"],
                    "id": p["id"],
                    "name": p["name"],
                    "description": p.get("description", ""),
                    "create_time": format_datetime(p["create_time"]),
                    "market_value": f"¥ {p['total_market_value']:,.2f}"
                    if p["total_market_value"]
                    else "¥ 0.00",
                    "fund_count": p["fund_count"] or 0,
                    "operation": operation_buttons,
                }
            )

        table_data.append(
            {
                "key": account["id"],
                "id": account["id"],
                "name": account["name"],
                "description": account.get("description", ""),
                "create_time": format_datetime(account["create_time"]),
                "operation": create_operation_buttons(
                    account["id"], "account", is_danger=True
                ),
                "children": portfolio_data,
            }
        )

    return table_data


def render_account_table(initial_data: List[Dict[str, Any]]) -> fac.AntdCard:
    """渲染账户表格卡片

    Args:
        initial_data: 初始账户数据列表

    Returns:
        AntdCard: 包含表格的卡片组件
        - 新建账户和组合按钮
        - 嵌套结构的数据表格
        - 表格分页和样式配置
    """
    expanded_keys = [account["id"] for account in initial_data]

    return fac.AntdCard(
        title="账户与组合管理",
        bordered=False,
        extra=[
            fac.AntdSpace(
                [
                    fac.AntdButton(
                        "新建账户",
                        type="primary",
                        icon=fac.AntdIcon(icon="antd-plus"),
                        id="add-account-btn",
                    ),
                    fac.AntdButton(
                        "新建组合",
                        type="primary",
                        icon=fac.AntdIcon(icon="antd-plus"),
                        id="add-portfolio-btn",
                    ),
                ]
            ),
        ],
        children=[
            fac.AntdTable(
                id="account-list",
                columns=[
                    {
                        "title": "ID",
                        "dataIndex": "id",
                        "key": "id",
                        "width": "20%",
                        "renderOptions": {"renderType": "copyable"},
                    },
                    {
                        "title": "名称",
                        "dataIndex": "name",
                        "key": "name",
                        "width": "15%",
                    },
                    {
                        "title": "描述",
                        "dataIndex": "description",
                        "key": "name",
                        "width": "15%",
                    },
                    {
                        "title": "创建时间",
                        "dataIndex": "create_time",
                        "key": "create_time",
                        "width": "15%",
                    },
                    {
                        "title": "市值",
                        "dataIndex": "market_value",
                        "key": "market_value",
                        "width": "10%",
                    },
                    {
                        "title": "基金数量",
                        "dataIndex": "fund_count",
                        "key": "fund_count",
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
                defaultExpandedRowKeys=expanded_keys,
                bordered=True,
                size="small",
                pagination={
                    "hideOnSinglePage": True,
                    "pageSize": 10,
                    "showSizeChanger": False,
                    "showQuickJumper": False,
                },
                style={
                    "marginTop": "8px",
                    "width": "100%",
                },
            ),
        ],
        bodyStyle={"padding": "12px"},
        style={"width": "100%"},
    )


@callback(
    Output("account-list", "data"),
    Input("account-store", "data"),
    prevent_initial_call=True,
)
def update_account_table(store_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Store数据更新时，更新账户表格"""
    return store_data


@callback(
    [
        Output("account-modal", "visible", allow_duplicate=True),
        Output("account-modal", "title"),
        Output("account-name-input", "value", allow_duplicate=True),
        Output("account-desc-input", "value", allow_duplicate=True),
        Output("portfolio-modal", "visible", allow_duplicate=True),
        Output("portfolio-modal", "title"),
        Output("portfolio-account-select", "value", allow_duplicate=True),
        Output("portfolio-name-input", "value", allow_duplicate=True),
        Output("portfolio-desc-input", "value", allow_duplicate=True),
        Output("account-delete-confirm-modal", "visible", allow_duplicate=True),
        Output("editing-account-id", "data", allow_duplicate=True),
        Output("portfolio-edit-mode", "data", allow_duplicate=True),
        Output("portfolio-account-form-item", "style", allow_duplicate=True),
    ],
    Input("account-list", "nClicksButton"),
    State("account-list", "clickedCustom"),
    State("account-store", "data"),
    prevent_initial_call=True,
)
def handle_button_click(nClicksButton, custom_info, accounts_data):
    """统一处理表格按钮点击事件"""
    if not nClicksButton or not custom_info:
        raise PreventUpdate

    object_type = custom_info.get("type")
    action = custom_info.get("action")
    object_id = custom_info.get("id")

    # 默认返回值
    default_return = (
        dash.no_update,  # account modal visible
        dash.no_update,  # account modal title
        dash.no_update,  # account name input
        dash.no_update,  # account desc input
        dash.no_update,  # portfolio modal visible
        dash.no_update,  # portfolio modal title
        dash.no_update,  # portfolio account select
        dash.no_update,  # portfolio name input
        dash.no_update,  # portfolio desc input
        dash.no_update,  # delete modal visible
        dash.no_update,  # editing id
        dash.no_update,  # portfolio edit mode
        dash.no_update,  # portfolio account form style
    )

    # 处理账户操作
    if object_type == "account":
        account = next((a for a in accounts_data if a["id"] == object_id), None)
        if not account:
            raise PreventUpdate

        if action == "edit":
            return (
                True,  # account modal visible
                "编辑账户",  # account modal title
                account["name"],  # account name input
                account["description"],  # account desc input
                False,  # portfolio modal visible
                dash.no_update,  # portfolio modal title
                dash.no_update,  # portfolio account select
                dash.no_update,  # portfolio name input
                dash.no_update,  # portfolio desc input
                False,  # delete modal visible
                object_id,  # editing id
                False,  # portfolio edit mode
                {"display": "none"},  # portfolio account form style
            )
        elif action == "delete":
            return (
                *default_return[:9],  # 保持其他输出不变
                True,  # delete modal visible
                object_id,  # editing id
                False,  # portfolio edit mode
                {"display": "none"},  # portfolio account form style
            )

    # 处理组合操作
    elif object_type == "portfolio":
        account_id = custom_info.get("accountId")
        portfolio = get_portfolio(object_id)
        if not portfolio:
            raise PreventUpdate

        if action == "edit":
            return (
                False,  # account modal visible
                dash.no_update,  # account modal title
                dash.no_update,  # account name input
                dash.no_update,  # account desc input
                True,  # portfolio modal visible
                "编辑组合",  # portfolio modal title
                account_id,  # portfolio account select
                portfolio["name"],  # portfolio name input
                portfolio["description"],  # portfolio desc input
                False,  # delete modal visible
                object_id,  # editing id
                True,  # portfolio edit mode
                {"display": "none"},  # portfolio account form style
            )
        elif action == "delete":
            return (
                *default_return[:9],  # 保持其他输出不变
                True,  # delete modal visible
                object_id,  # editing id
                False,  # portfolio edit mode
                {"display": "none"},  # portfolio account form style
            )

    return default_return
