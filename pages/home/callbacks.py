"""首页回调函数模块

处理首页的动态更新:
- 统计数据更新: 更新所有数据卡片的显示值
- 图表数据更新: 更新资产配置和收益走势图表
"""

import logging
from typing import Any, Dict, Tuple

import plotly.graph_objects as go
from dash import Input, Output, callback
from dash.exceptions import PreventUpdate

from models.database import get_statistics
from .utils import format_money, format_percent

# 添加日志配置
logger = logging.getLogger(__name__)

# 图表配置常量
CHART_COLORS = ["#1890ff", "#52c41a", "#faad14", "#f5222d", "#722ed1"]
CHART_LAYOUT = {
    "margin": dict(l=20, r=20, t=20, b=20),
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
}


@callback(
    [
        Output("total-assets", "children"),
        Output("fund-count", "children"),
        Output("total-return-rate", "children"),
        Output("account-count", "children"),
        Output("daily-return", "children"),
    ],
    Input("home-statistics-store", "data"),
    prevent_initial_call=True,
)
def update_statistics(data: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    """更新统计数据显示

    Args:
        data: 包含所有统计数据的字典

    Returns:
        tuple: 包含所有更新值的元组:
        - 总资产显示值
        - 基金数量显示值
        - 总收益率显示值
        - 账户数量显示值
        - 日收益显示值

    Raises:
        PreventUpdate: 当输入数据无效时
    """
    if not data:
        logger.warning("统计数据为空")
        raise PreventUpdate

    try:
        return (
            format_money(data.get("total_assets", 0)),
            str(data.get("fund_count", 0)),
            format_percent(data.get("total_return_rate", 0)),
            str(data.get("account_count", 0)),
            format_money(data.get("daily_return", 0)),
        )
    except Exception as e:
        logger.error("更新统计数据失败: %s", str(e))
        raise PreventUpdate


@callback(
    Output("asset-allocation-pie", "figure"),
    Input("home-statistics-store", "data"),
    prevent_initial_call=True,
)
def update_asset_allocation(data: Dict[str, Any]):
    """更新资产配置图表

    Args:
        data: 统计数据字典

    Returns:
        plotly.Figure: 更新后的饼图
    """
    if not data:
        raise PreventUpdate

    # 这里添加资产配置图表的逻辑
    return go.Figure()


@callback(
    Output("performance-line", "figure"),
    Input("home-statistics-store", "data"),
    prevent_initial_call=True,
)
def update_performance_chart(data: Dict[str, Any]):
    """更新收益走势图表

    Args:
        data: 统计数据字典

    Returns:
        plotly.Figure: 更新后的折线图
    """
    if not data:
        raise PreventUpdate

    # 这里添加收益走势图表的逻辑
    return go.Figure()
