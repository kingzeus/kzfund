"""账户管理页面主渲染模块

页面结构:
1. Store组件
   - account-store: 存储账户数据
   - editing-account-id: 存储正在编辑的账户ID

2. 页面标题
   - 图标 + 文字标题

3. 主要内容
   - 账户表格(嵌套显示组合数据)

4. 弹窗组件
   - 账户编辑弹窗
   - 组合编辑弹窗
   - 删除确认弹窗
"""

import feffery_antd_components as fac
from dash import dcc, html

from pages.account.account_modal import render_account_modal
from pages.account.delete_modal import render_delete_confirm_modal
from pages.account.portfolio_modal import render_portfolio_modal
from pages.account.table import get_account_table_data, render_account_table


def render_account_page() -> html.Div:
    """渲染账户管理页面

    Returns:
        包含完整页面结构的Div组件
    """
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
                                icon="antd-partition",
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
