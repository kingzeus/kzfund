from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import dash
from dash import html, dcc, Input, Output, State, callback, ALL
import feffery_antd_components as fac
from dash.exceptions import PreventUpdate

from models.database import (
    get_accounts,
    add_account,
    get_portfolios,
    update_account,
    delete_account,
    add_portfolio,
    delete_portfolio,
    get_portfolio,
    update_portfolio,
)
from utils.datetime import format_datetime


# ============= 常量定义 =============
NAME_MIN_LENGTH = 2
NAME_MAX_LENGTH = 20


# ============= 工具函数 =============
def validate_name(name: Optional[str], field_name: str = "名称") -> Tuple[str, str]:
    """通用的名称验证函数

    Args:
        name: 要验证的名称
        field_name: 字段名称，用于错误消息

    Returns:
        验证状态和帮助信息的元组
    """
    if not name:
        return "error", f"请输入{field_name}"
    if len(name) < NAME_MIN_LENGTH:
        return "error", f"{field_name}至少需要{NAME_MIN_LENGTH}个字符"
    if len(name) > NAME_MAX_LENGTH:
        return "error", f"{field_name}不能超过{NAME_MAX_LENGTH}个字符"
    return "success", ""


def create_operation_buttons(
    object_id: str,
    action_type: str,
    account_id: Optional[str] = None,
    is_danger: bool = False,
) -> List[Dict[str, Any]]:
    """创建操作按钮配置

    Args:
        object_id: 对象ID
        action_type: 对象类型 ('account' 或 'portfolio')
        account_id: 账户ID（仅用于组合）
        is_danger: 是否为危险操作按钮

    Returns:
        按钮配置列表
    """
    buttons = []

    # 编辑按钮
    buttons.append(
        {
            "icon": "antd-edit",
            "iconRenderer": "AntdIcon",
            "type": "link",
            "custom": {
                "id": object_id,
                "action": "edit",
                "type": action_type,
                **({"accountId": account_id} if account_id else {}),
            },
        }
    )

    # 删除按钮
    if is_danger:
        buttons.append(
            {
                "icon": "antd-delete",
                "iconRenderer": "AntdIcon",
                "type": "link",
                "danger": True,
                "custom": {
                    "id": object_id,
                    "action": "delete",
                    "type": action_type,
                    **({"accountId": account_id} if account_id else {}),
                },
            }
        )

    return buttons


# ============= 数据处理函数 =============
def get_account_table_data() -> List[Dict[str, Any]]:
    """从数据库获取账户信息并转换为表格显示格式（包含嵌套的组合数据）"""
    accounts = get_accounts()
    table_data = []

    for account in accounts:
        # 获取该账户下的所有组合（已经在数据库层面排序）
        portfolios = get_portfolios(account["id"])
        portfolio_data = []

        # 处理组合数据
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

        # 处理账户数据
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


# ============= UI 组件渲染函数 =============
def render_account_table(initial_data: List[Dict[str, Any]]) -> fac.AntdCard:
    """渲染账户表格卡片（包含嵌套的组合数据）"""
    # 获取所有账户 id 作为默认展开的行 key
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
                defaultExpandedRowKeys=expanded_keys,  # 添加默认展开的行 key
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
        width=500,
        okText="确定",
        cancelText="取消",
        children=[
            # 添加一个 Store 来标记是否为编辑模式
            dcc.Store(id="portfolio-edit-mode", data=False),
            fac.AntdForm(
                labelCol={"span": 6},
                wrapperCol={"span": 18},
                children=[
                    # 账户选择器，只在新建模式下显示
                    fac.AntdFormItem(
                        fac.AntdSelect(
                            id="portfolio-account-select",
                            placeholder="请选择账户",
                            options=[],
                            style={"width": "100%"},
                        ),
                        label="所属账户",
                        required=True,
                        id="portfolio-account-form-item",
                        style={"display": "none"},  # 默认隐藏
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="portfolio-name-input",
                            placeholder="请输入组合名称",
                            allowClear=True,
                        ),
                        label="组合名称",
                        required=True,
                        id="portfolio-name-form-item",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="portfolio-desc-input",
                            mode="text-area",
                            placeholder="请输入组合描述",
                            allowClear=True,
                            autoSize={"minRows": 3, "maxRows": 5},
                        ),
                        label="组合描述",
                        id="portfolio-desc-form-item",
                    ),
                ],
            ),
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
            # 主要内容区域 - 只保留账户表格
            fac.AntdRow(
                fac.AntdCol(
                    render_account_table(initial_accounts),
                    span=24,
                    style={"padding": "8px"},
                ),
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
            # 编辑模式
            update_account(editing_id, name, description)
        else:
            # 创建模式 - 会自动创建默认投资组合
            add_account(name, description)

        # 获取更新后的账户列表（包含新创建的默认组合）
        return get_account_table_data(), False, "", ""
    return get_account_table_data(), dash.no_update, dash.no_update, dash.no_update


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
        Output("delete-confirm-modal", "visible", allow_duplicate=True),
        Output("editing-account-id", "data", allow_duplicate=True),
        Output("portfolio-edit-mode", "data", allow_duplicate=True),  # 添加编辑模式输出
        Output(
            "portfolio-account-form-item", "style", allow_duplicate=True
        ),  # 添加样式输出
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
        p["create_time"] = format_datetime(p["create_time"])
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
    """Store数据更新时，更新账户表格"""
    return store_data


# 添加新的回调函数来更新账户选择器的选项
@callback(
    [
        Output("portfolio-modal", "visible"),
        Output("portfolio-account-select", "options"),
        Output("portfolio-account-form-item", "style"),  # 添加样式输出
        Output("portfolio-edit-mode", "data"),  # 添加编辑模式标记输出
    ],
    Input("add-portfolio-btn", "nClicks"),
    State("account-store", "data"),
    prevent_initial_call=True,
)
def show_portfolio_modal(n_clicks, accounts_data):
    """显示新建组合对话框"""
    if not n_clicks:
        raise PreventUpdate

    # 构建账户选择器的选项
    account_options = [
        {
            "label": account["name"],
            "value": account["id"],
        }
        for account in accounts_data
    ]

    return True, account_options, {"display": "block"}, False  # 新建模式显示账户选择器


# 添加组合创建的回调
@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("portfolio-modal", "visible", allow_duplicate=True),
        Output("portfolio-account-select", "value", allow_duplicate=True),
        Output("portfolio-name-input", "value", allow_duplicate=True),
        Output("portfolio-desc-input", "value", allow_duplicate=True),
    ],
    Input("portfolio-modal", "okCounts"),
    [
        State("portfolio-edit-mode", "data"),
        State("portfolio-account-select", "value"),
        State("portfolio-name-input", "value"),
        State("portfolio-desc-input", "value"),
        State("editing-account-id", "data"),
    ],
    prevent_initial_call=True,
)
def handle_portfolio_create_or_edit(
    ok_counts, is_edit_mode, account_id, name, description, editing_id
):
    """处理组合创建或编辑"""
    if not ok_counts or not name:
        raise PreventUpdate

    if is_edit_mode and editing_id:
        # 编辑模式
        update_portfolio(
            editing_id,
            {
                "name": name,
                "description": description,
            },
        )
    else:
        # 创建模式
        if not account_id:
            raise PreventUpdate
        add_portfolio(
            account_id=account_id,
            name=name,
            description=description,
            is_default=False,
        )

    # 更新数据并关闭对话框
    return get_account_table_data(), False, None, "", ""


# 添加组合名称验证的回调
@callback(
    [
        Output("portfolio-name-form-item", "validateStatus"),
        Output("portfolio-name-form-item", "help"),
    ],
    Input("portfolio-name-input", "value"),
    prevent_initial_call=True,
)
def validate_portfolio_name(name: Optional[str]) -> Tuple[str, str]:
    """验证组合名"""
    if not name:
        return "error", "请输入组合名称"
    if len(name) < 2:
        return "error", "组合名称至少需要2个字符"
    if len(name) > 20:
        return "error", "组合名称不能超过20个字符"
    return "success", ""


# 修改删除确认对话框的回调
@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("delete-confirm-modal", "visible", allow_duplicate=True),
    ],
    Input("delete-confirm-modal", "okCounts"),
    [
        State("editing-account-id", "data"),
        State("account-list", "clickedCustom"),  # 添加这个状态来获取对象类型信息
    ],
    prevent_initial_call=True,
)
def handle_delete_confirm(ok_counts, object_id, custom_info):
    """处理删除确认"""
    if not ok_counts or not object_id:
        raise PreventUpdate

    success = False
    if custom_info and custom_info.get("type") == "portfolio":
        # 删除组合
        success = delete_portfolio(object_id)
    else:
        # 删除账户
        success = delete_account(object_id)

    if success:
        return get_account_table_data(), False
    else:
        return dash.no_update, False
