"""首页主渲染模块

页面结构:
1. Store组件
   - statistics-store: 存储统计数据

2. 页面标题
   - 图标 + 文字标题

3. 数据概览
   - 四个数据卡片

4. 图表区域
   - 资产配置图
   - 收益走势图
"""

from dash import html, dcc
import feffery_antd_components as fac

from models.database import get_statistics
from .overview import (
    render_total_assets_card,
    render_fund_count_card,
    render_return_rate_card,
    render_account_count_card,
)
from .charts import render_asset_allocation_chart, render_performance_chart
from .utils import ICON_STYLES
from . import callbacks  # 添加这行导入


def render_home_page() -> html.Div:
    """渲染首页

    Returns:
        包含完整页面结构的Div组件
    """
    # 获取初始统计数据
    initial_stats = get_statistics()

    return html.Div(
        [
            # Store 组件
            dcc.Store(id="statistics-store", data=initial_stats),
            # 页面标题
            fac.AntdRow(
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdIcon(
                                icon="HomeOutlined",
                                style=ICON_STYLES,
                            ),
                            "仪表盘",
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
            # 数据概览卡片
            fac.AntdRow(
                [
                    fac.AntdCol(
                        render_total_assets_card(),
                        span=6,
                        style={"padding": "12px"},
                    ),
                    fac.AntdCol(
                        render_fund_count_card(),
                        span=6,
                        style={"padding": "8px"},
                    ),
                    fac.AntdCol(
                        render_return_rate_card(),
                        span=6,
                        style={"padding": "8px"},
                    ),
                    fac.AntdCol(
                        render_account_count_card(initial_stats),
                        span=6,
                        style={"padding": "8px"},
                    ),
                ]
            ),
            # 图表区域
            fac.AntdRow(
                [
                    fac.AntdCol(
                        render_asset_allocation_chart(),
                        span=12,
                        style={"padding": "8px"},
                    ),
                    fac.AntdCol(
                        render_performance_chart(),
                        span=12,
                        style={"padding": "8px"},
                    ),
                ]
            ),
        ],
        style={"padding": "24px"},
    )
