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


def get_account_table_data() -> List[Dict[str, Any]]:
    """从数据库获取账户信息并转换为表格显示格式"""

    accounts = get_accounts()
    # 转换为表格显示格式
    table_data = []
    for account in accounts:
        # 处理创建时间
        create_time = account["create_time"]
        if isinstance(create_time, datetime):
            # 如果已经是datetime对象，直接格式化
            formatted_time = create_time.strftime("%Y-%m-%d %H:%M")
        else:
            # 如果是字符串，先转换为datetime
            try:
                formatted_time = datetime.fromisoformat(str(create_time)).strftime(
                    "%Y-%m-%d %H:%M"
                )
            except (ValueError, TypeError):
                formatted_time = "未知时间"
        description = account.get("description", "")
        table_data.append(
            {
                "key": account["id"],  # 确保key是字符串
                "raw_name": account["name"],  # 添加原始名称
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
                    {
                        "title": "账户名称",
                        "dataIndex": "name",
                        "key": "name",
                    },
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
                    "hideOnSinglePage": True,  # 单页时隐藏分页器
                    "pageSize": 10,  # 每页显示数量
                    "showSizeChanger": False,  # 隐藏每页显示数量选择器
                    "showQuickJumper": False,  # 隐藏页面跳转输入框
                },
                style={
                    "marginTop": "8px",
                    "width": "100%",
                },
            ),
        ],
        bodyStyle={
            "padding": "12px",
        },
    )


def render_account_page() -> html.Div:
    """渲染账户管理页面"""
    initial_accounts = get_account_table_data()

    return html.Div(
        [
            dcc.Store(id="account-store", data=initial_accounts),
            # 添加存储当前编辑的账户ID的 Store
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
            # 账户列表和组合管理
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
                        fac.AntdCard(
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
                                        {
                                            "title": "组合名称",
                                            "dataIndex": "name",
                                            "key": "name",
                                        },
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
                                            "title": "金数量",
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
                                                    {
                                                        "text": "查看",
                                                        "type": "link",
                                                        "icon": "EyeOutlined",
                                                    },
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
                        ),
                        span=16,
                        style={"padding": "8px"},
                    ),
                ]
            ),
            # 新建账户对话框
            fac.AntdModal(
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
                                    autoSize={
                                        "minRows": 3,
                                        "maxRows": 5,
                                    },
                                ),
                                label="账户描述",
                                id="account-desc-form-item",
                            ),
                        ],
                    )
                ],
            ),
            # 新建组合对话框
            fac.AntdModal(
                id="portfolio-modal",
                title="新建组合",
                visible=False,
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
            ),
            # 确认删除对话框
            fac.AntdModal(
                id="delete-confirm-modal",
                title="确认删除",
                visible=False,
                children="确定要删除这个账户吗？删除后无法恢复。",
                okText="确定",
                cancelText="取消",
                renderFooter=True,
                maskClosable=False,
            ),
        ],
        style={"padding": "24px"},
    )

# 修改显示账户对话框回调
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
        return True, "", "", ""  # 显示对话框并清空输入，同时清空编辑ID
    return dash.no_update


# 添加表单验证回调
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


# 修改创建账户回调
@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("account-modal", "visible", allow_duplicate=True),
        Output("account-name-input", "value", allow_duplicate=True),
        Output("account-desc-input", "value", allow_duplicate=True),
    ],
    [
        Input("account-modal", "okCounts"),
    ],
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
        if editing_id:  # 编辑模式
            update_account(editing_id, name, description)
        else:  # 创建模式
            add_account(name, description)

        # 获取更新后的账户列表
        updated_accounts = get_account_table_data()
        # 关闭对话框并清空输入
        return updated_accounts, False, "", ""

    return get_account_table_data(), dash.no_update, dash.no_update, dash.no_update


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

    # 格式化数据
    for p in portfolios:
        p["create_time"] = datetime.fromisoformat(p["create_time"]).strftime(
            "%Y-%m-%d %H:%M"
        )
        p["market_value"] = (
            f"¥ {p['total_market_value']:,.2f}" if p["total_market_value"] else "¥ 0.00"
        )
        p["fund_count"] = p["fund_count"] or 0

    return portfolios

# 添加Store数据更新到Table的回调
@callback(
    Output("account-list", "data"),
    Input("account-store", "data"),
    prevent_initial_call=True,
)
def update_account_table(store_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """当Store数据更新时，更新账户表格"""
    return store_data

# 添加编辑按钮回调
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
    if not any(clicks) or all(x is None for x in clicks):
        raise PreventUpdate

    triggered_id = dash.callback_context.triggered[0]["prop_id"]
    account_id = json.loads(triggered_id.split(".")[0])["index"]

    # 找到对应的账户数据
    account = next((a for a in accounts_data if a["key"] == account_id), None)
    if not account:
        raise PreventUpdate

    return True, "编辑账户", account["raw_name"], account["description"], account_id


# 添加删除按钮回调
@callback(
    [
        Output("delete-confirm-modal", "visible"),
        Output("editing-account-id", "data", allow_duplicate=True),
    ],
    [Input({"type": "delete-account-btn", "index": ALL}, "nClicks")],
    prevent_initial_call=True,
)
def show_delete_confirm(clicks):
    if not any(clicks) or all(x is None for x in clicks):
        raise PreventUpdate

    triggered_id = dash.callback_context.triggered[0]["prop_id"]
    account_id = json.loads(triggered_id.split(".")[0])["index"]
    return True, account_id


# 添加删除确认回调
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
    if not ok_counts or not account_id:
        raise PreventUpdate

    success = delete_account(account_id)
    if success:
        return get_account_table_data(), False
    else:
        return dash.no_update, False
