"""首页主渲染模块

页面结构:
1. Store组件
   - home-statistics-store: 存储统计数据

2. 页面标题
   - 图标 + 文字标题

3. 数据概览
   - 四个数据卡片

4. 图表区域
   - 资产配置图
   - 收益走势图
"""

import feffery_antd_components as fac
from dash import dcc, html
from dash import Input, Output, callback

from config import PAGE_CONFIG
from models.database import get_statistics
from pages.home.charts import render_asset_allocation_chart, render_performance_chart
from pages.home.home_overview import (
    render_account_count_card,
    render_fund_data_card,
    render_return_rate_card,
    render_today_fund_card,
    render_today_task_card,
    render_total_assets_card,
)

from .utils import ICON_STYLES


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
            dcc.Store(id="home-statistics-store", data=initial_stats),
            # 添加30秒定时刷新组件
            dcc.Interval(
                id="home-interval",
                interval=PAGE_CONFIG["HOME_INTERVAL_TIME"],
            ),
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
            # 系统数据概览卡片
            fac.AntdRow(
                [
                    # 当前系统基金数据
                    fac.AntdCol(
                        render_fund_data_card(initial_stats),
                        span=6,
                        style={"padding": "8px"},
                    ),
                    # 今日更新基金数据
                    fac.AntdCol(
                        render_today_fund_card(initial_stats),
                        span=6,
                        style={"padding": "8px"},
                    ),
                    fac.AntdCol(
                        render_today_task_card(initial_stats),
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


@callback(
    Output("home-statistics-store", "data"),
    Input("home-interval", "n_intervals"),
)
def update_statistics_store(n: int) -> dict:
    """定时更新统计数据

    Args:
        n: 定时器触发次数

    Returns:
        更新后的统计数据字典
    """

    return get_statistics()
