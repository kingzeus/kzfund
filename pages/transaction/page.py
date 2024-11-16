"""交易记录页面主渲染模块

页面结构:
1. Store组件
   - transaction-store: 存储交易记录数据
   - editing-transaction-id: 存储正在编辑的交易记录ID

2. 页面标题
   - 图标 + 文字标题

3. 主要内容
   - 交易记录表格

4. 弹窗组件
   - 交易记录编辑弹窗
   - 删除确认弹窗
"""

import feffery_antd_components as fac
from dash import dcc, html

from models.database import get_transactions

from .delete_modal import render_delete_confirm_modal
from .modal import render_transaction_modal
from .table import render_transaction_table

# 页面样式常量
PAGE_PADDING = 24
ICON_STYLES = {"fontSize": "24px", "marginRight": "8px"}


def render_transaction_page() -> html.Div:
    """渲染交易记录页面

    Returns:
        包含完整页面结构的Div组件
    """
    initial_transactions = get_transactions()

    return html.Div(
        [
            # Store 组件
            dcc.Store(id="transaction-store", data=initial_transactions),
            dcc.Store(id="editing-transaction-id", data=""),
            # 页面标题
            fac.AntdRow(
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdIcon(
                                icon="antd-calendar",
                                style=ICON_STYLES,
                            ),
                            "交易记录",
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
                    render_transaction_table(initial_transactions),
                    span=24,
                    style={"padding": f"{PAGE_PADDING}px"},
                ),
            ),
            # 对话框组件
            render_transaction_modal(),
            render_delete_confirm_modal(),
        ],
        style={"padding": f"{PAGE_PADDING}px"},
    )
