from typing import Dict, Any, List, Optional, Tuple
import dash
from dash import html, dcc, Input, Output, State, callback, ALL
import feffery_antd_components as fac
from datetime import datetime
import json
from dash.exceptions import PreventUpdate

from models.database import (
    get_accounts,
    add_account,
    get_portfolios,
    update_account,
    delete_account,
)

# ============= 数据处理函数 =============
def get_account_table_data() -> List[Dict[str, Any]]:
    """从数据库获取账户信息并转换为表格显示格式"""
    accounts = get_accounts()
    table_data = []
    for account in accounts:
        # 处理创建时间
        create_time = account["create_time"]
        if isinstance(create_time, datetime):
            formatted_time = create_time.strftime("%Y-%m-%d %H:%M")
        else:
            try:
                formatted_time = datetime.fromisoformat(str(create_time)).strftime(
                    "%Y-%m-%d %H:%M"
                )
            except (ValueError, TypeError):
                formatted_time = "未知时间"

        description = account.get("description", "")
        table_data.append(
            {
                "key": account["id"],
                "raw_name": account["name"],
                "name": fac.AntdTooltip(account["name"], title=description)
                if len(description) > 0
                else account["name"],
                "description": account.get("description", ""),
                "create_time": fac.AntdTooltip(formatted_time, title=description)
                if len(description) > 0
                else formatted_time,
                "operation": fac.AntdSpace(
                    [
                        fac.AntdButton(
                            icon=fac.AntdIcon(icon="antd-edit"),
                            id={"type": "edit-account-btn", "index": account["id"]},
                        ),
                        fac.AntdButton(
                            icon=fac.AntdIcon(icon="antd-delete"),
                            danger=True,
                            id={"type": "delete-account-btn", "index": account["id"]},
                        ),
                    ]
                ),
            }
        )
    return table_data


# ============= UI 组件渲染函数 =============
def render_account_table(initial_data: List[Dict[str, Any]]) -> fac.AntdCard:
    """渲染账户表格卡片"""
    return fac.AntdCard(
        title="账户列表",
        bordered=False,
        extra=[
            fac.AntdButton(
                "新建账户",
                type="primary",
                icon=fac.AntdIcon(icon="antd-plus"),
                id="add-account-btn",
            ),
        ],
        children=[
            fac.AntdTable(
                id="account-list",
                columns=[
                    {"title": "账户名称", "dataIndex": "name", "key": "name"},
                    {
                        "title": "创建时间",
                        "dataIndex": "create_time",
                        "key": "create_time",
                    },
                    {
                        "title": "操作",
                        "dataIndex": "operation",
                        "key": "operation",
                        "width": 120,
                    },
                ],
                data=initial_data,
                bordered=True,
                size="small",
                pagination={
                    "hideOnSinglePage": True,
                    "pageSize": 10,
                    "showSizeChanger": False,
                    "showQuickJumper": False,
                },
                style={"marginTop": "8px", "width": "100%"},
            ),
        ],
        bodyStyle={"padding": "12px"},
    )


def render_portfolio_table() -> fac.AntdCard:
    """渲染组合管理表格"""
    return fac.AntdCard(
        title="组合管理",
        bordered=False,
        extra=[
            fac.AntdButton(
                "新建组合",
                type="primary",
                icon=fac.AntdIcon(icon="antd-plus"),
                id="add-portfolio-btn",
            ),
        ],
        children=[
            fac.AntdTable(
                id="portfolio-table",
                columns=[
                    {"title": "组合名称", "dataIndex": "name", "key": "name"},
                    {
                        "title": "创建时间",
                        "dataIndex": "create_time",
                        "key": "create_time",
                    },
                    {
                        "title": "总市值",
                        "dataIndex": "market_value",
                        "key": "market_value",
                    },
                    {
                        "title": "基金数量",
                        "dataIndex": "fund_count",
                        "key": "fund_count",
                    },
                    {
                        "title": "操作",
                        "dataIndex": "operation",
                        "key": "operation",
                        "width": 180,
                        "render": {
                            "type": "button-group",
                            "buttons": [
                                {"text": "查看", "type": "link", "icon": "EyeOutlined"},
                                {
                                    "text": "编辑",
                                    "type": "link",
                                    "icon": "EditOutlined",
                                },
                                {
                                    "text": "删除",
                                    "type": "link",
                                    "danger": True,
                                    "icon": "DeleteOutlined",
                                },
                            ],
                        },
                    },
                ],
                data=[],
                bordered=True,
            ),
        ],
    )


def render_account_modal() -> fac.AntdModal:
    """渲染账户编辑对话框"""
    return fac.AntdModal(
        id="account-modal",
        title="新建账户",
        visible=False,
        maskClosable=False,
        width=500,
        renderFooter=True,
        okText="确定",
        cancelText="取消",
        children=[
            fac.AntdForm(
                id="account-form",
                labelCol={"span": 6},
                wrapperCol={"span": 18},
                children=[
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="account-name-input",
                            placeholder="请输入账户名称",
                            allowClear=True,
                        ),
                        label="账户名称",
                        required=True,
                        id="account-name-form-item",
                        validateStatus="validating",
                        help="",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="account-desc-input",
                            mode="text-area",
                            placeholder="请输入账户描述",
                            allowClear=True,
                            autoSize={"minRows": 3, "maxRows": 5},
                        ),
                        label="账户描述",
                        id="account-desc-form-item",
                    ),
                ],
            )
        ],
    )


def render_portfolio_modal() -> fac.AntdModal:
    """渲染组合编辑对话框"""
    return fac.AntdModal(
        id="portfolio-modal",
        title="新建组合",
        visible=False,
        renderFooter=True,
        maskClosable=False,
        children=[
            fac.AntdForm(
                [
                    fac.AntdFormItem(
                        fac.AntdInput(id="portfolio-name-input"),
                        label="组合名称",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="portfolio-desc-input",
                            mode="text-area",
                        ),
                        label="组合描述",
                    ),
                    fac.AntdFormItem(
                        fac.AntdSwitch(id="portfolio-default-switch"),
                        label="设为默认组合",
                    ),
                ]
            )
        ],
    )


def render_delete_confirm_modal() -> fac.AntdModal:
    """渲染删除确认对话框"""
    return fac.AntdModal(
        id="delete-confirm-modal",
        title="确认删除",
        visible=False,
        children="确定要删除这个账户吗？删除后无法恢复。",
        okText="确定",
        cancelText="取消",
        renderFooter=True,
        maskClosable=False,
    )


def render_account_page() -> html.Div:
    """渲染账户管理页面"""
    initial_accounts = get_account_table_data()

    return html.Div(
        [
            # Store 组件
            dcc.Store(id="account-store", data=initial_accounts),
            dcc.Store(id="editing-account-id", data=""),
            # 页面标题
            fac.AntdRow(
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdIcon(
                                icon="UserOutlined",
                                style={"fontSize": "24px", "marginRight": "8px"},
                            ),
                            "账户与组合管理",
                        ],
                        style={
                            "fontSize": "20px",
                            "fontWeight": "bold",
                            "padding": "16px 0",
                            "display": "flex",
                            "alignItems": "center",
                        },
                    ),
                    span=24,
                )
            ),
            # 主要内容区域
            fac.AntdRow(
                [
                    # 左侧账户列表
                    fac.AntdCol(
                        render_account_table(initial_accounts),
                        span=8,
                        style={"padding": "8px"},
                    ),
                    # 右侧组合管理
                    fac.AntdCol(
                        render_portfolio_table(),
                        span=16,
                        style={"padding": "8px"},
                    ),
                ]
            ),
            # 对话框组件
            render_account_modal(),
            render_portfolio_modal(),
            render_delete_confirm_modal(),
        ],
        style={"padding": "24px"},
    )


# ============= 回调函数 =============
# 账户相关回调
@callback(
    [
        Output("account-modal", "visible", allow_duplicate=True),
        Output("account-name-input", "value", allow_duplicate=True),
        Output("account-desc-input", "value", allow_duplicate=True),
        Output("editing-account-id", "data", allow_duplicate=True),
    ],
    Input("add-account-btn", "nClicks"),
    prevent_initial_call=True,
)
def show_account_modal(n_clicks: Optional[int]) -> Tuple[bool, str, str, str]:
    """显示新建账户对话框"""
    if n_clicks:
        return True, "", "", ""
    return dash.no_update


@callback(
    [
        Output("account-name-form-item", "validateStatus"),
        Output("account-name-form-item", "help"),
    ],
    Input("account-name-input", "value"),
    prevent_initial_call=True,
)
def validate_account_name(name: Optional[str]) -> Tuple[str, str]:
    """验证账户名称"""
    if not name:
        return "error", "请输入账户名称"
    if len(name) < 2:
        return "error", "账户名称至少需要2个字符"
    if len(name) > 20:
        return "error", "账户名称不能超过20个字符"
    return "success", ""


@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("account-modal", "visible", allow_duplicate=True),
        Output("account-name-input", "value", allow_duplicate=True),
        Output("account-desc-input", "value", allow_duplicate=True),
    ],
    [Input("account-modal", "okCounts")],
    [
        State("account-name-input", "value"),
        State("account-desc-input", "value"),
        State("account-name-form-item", "validateStatus"),
        State("editing-account-id", "data"),
    ],
    prevent_initial_call=True,
)
def handle_account_create_or_edit(
    ok_counts: Optional[int],
    name: Optional[str],
    description: Optional[str],
    validate_status: str,
    editing_id: str,
) -> Tuple[List[Dict[str, Any]], bool, str, str]:
    """处理账户创建编辑"""
    if ok_counts and name and validate_status == "success":
        if editing_id:
            update_account(editing_id, name, description)
        else:
            add_account(name, description)
        return get_account_table_data(), False, "", ""
    return get_account_table_data(), dash.no_update, dash.no_update, dash.no_update


@callback(
    [
        Output("account-modal", "visible", allow_duplicate=True),
        Output("account-modal", "title"),
        Output("account-name-input", "value", allow_duplicate=True),
        Output("account-desc-input", "value", allow_duplicate=True),
        Output("editing-account-id", "data"),
    ],
    [Input({"type": "edit-account-btn", "index": ALL}, "nClicks")],
    [State("account-store", "data")],
    prevent_initial_call=True,
)
def show_edit_modal(clicks, accounts_data):
    """显示编辑账户对话框"""
    if not any(clicks) or all(x is None for x in clicks):
        raise PreventUpdate

    triggered_id = dash.callback_context.triggered[0]["prop_id"]
    account_id = json.loads(triggered_id.split(".")[0])["index"]

    account = next((a for a in accounts_data if a["key"] == account_id), None)
    if not account:
        raise PreventUpdate

    return True, "编辑账户", account["raw_name"], account["description"], account_id


@callback(
    [
        Output("delete-confirm-modal", "visible"),
        Output("editing-account-id", "data", allow_duplicate=True),
    ],
    [Input({"type": "delete-account-btn", "index": ALL}, "nClicks")],
    prevent_initial_call=True,
)
def show_delete_confirm(clicks):
    """显示删除确认对话框"""
    if not any(clicks) or all(x is None for x in clicks):
        raise PreventUpdate

    triggered_id = dash.callback_context.triggered[0]["prop_id"]
    account_id = json.loads(triggered_id.split(".")[0])["index"]
    return True, account_id

@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("delete-confirm-modal", "visible", allow_duplicate=True),
    ],
    Input("delete-confirm-modal", "okCounts"),
    State("editing-account-id", "data"),
    prevent_initial_call=True,
)
def handle_account_delete(ok_counts, account_id):
    """处理账户删除"""
    if not ok_counts or not account_id:
        raise PreventUpdate

    success = delete_account(account_id)
    if success:
        return get_account_table_data(), False
    else:
        return dash.no_update, False

# 组合相关回调
@callback(
    Output("portfolio-table", "data"),
    [Input("account-list", "selectedRowKeys")],
    prevent_initial_call=True,
)
def update_portfolio_list(
    selected_account: Optional[List[str]],
) -> List[Dict[str, Any]]:
    """更新组合列表"""
    if not selected_account:
        return []

    account_id = selected_account[0]
    portfolios = get_portfolios(account_id)

    for p in portfolios:
        p["create_time"] = datetime.fromisoformat(p["create_time"]).strftime(
            "%Y-%m-%d %H:%M"
        )
        p["market_value"] = (
            f"¥ {p['total_market_value']:,.2f}" if p["total_market_value"] else "¥ 0.00"
        )
        p["fund_count"] = p["fund_count"] or 0

    return portfolios


@callback(
    Output("account-list", "data"),
    Input("account-store", "data"),
    prevent_initial_call=True,
)
def update_account_table(store_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """当Store数据更新时，更新账户表格"""
    return store_data
