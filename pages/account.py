from typing import Dict, Any
import dash
from dash import html
import feffery_antd_components as fac
from dash import Input, Output, callback
from utils.db import get_db
from datetime import datetime


def create_account_page() -> html.Div:
    """创建账户管理页面"""
    return html.Div(
        [
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
                        fac.AntdCard(
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
                                            "title": "操作",
                                            "dataIndex": "operation",
                                            "key": "operation",
                                            "width": 120,
                                            "render": {
                                                "type": "button-group",
                                                "buttons": [
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
                                    style={"marginTop": "8px"},
                                ),
                            ],
                        ),
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
                children=[
                    fac.AntdForm(
                        [
                            fac.AntdFormItem(
                                fac.AntdInput(id="account-name-input"),
                                label="账户名称",
                            ),
                            fac.AntdFormItem(
                                fac.AntdInput(
                                    id="account-desc-input",
                                    mode="text-area",
                                ),
                                label="账户描述",
                            ),
                        ]
                    )
                ],
            ),
            # 新建组���对话框
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
        ],
        style={"padding": "24px"},
    )

# 添加回调函数
@callback(
    [
        Output("account-list", "data"),
        Output("account-modal", "visible"),
    ],
    [
        Input("add-account-btn", "nClicks"),
        Input("account-name-input", "value"),
        Input("account-desc-input", "value"),
    ],
    prevent_initial_call=True,
)
def handle_account_operations(n_clicks, name, description):
    """处理账户相关操作"""
    if n_clicks:
        db = get_db()
        if name:
            # 添加新账户
            db.add_account(name, description)
            # 刷新账户列表
            accounts = db.get_accounts()
            return accounts, False

    # 获取账户列表
    accounts = get_db().get_accounts()
    return accounts, dash.no_update


@callback(
    Output("portfolio-table", "data"),
    [Input("account-list", "selectedRowKeys")],
    prevent_initial_call=True,
)
def update_portfolio_list(selected_account):
    """更新组合列表"""
    if not selected_account:
        return []

    account_id = selected_account[0]
    portfolios = get_db().get_portfolios(account_id)

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
