"""图表组件模块

提供首页的图表组件:
- 资产配置饼图
- 收益走势折线图
"""

from dash import html, dcc
import feffery_antd_components as fac

from .utils import CARD_STYLES, CARD_HOVER_STYLES

# ============= 图表配置常量 =============
CHART_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}

CHART_STYLE = {
    "height": "360px",
}

CHART_CARD_HEAD_STYLE = {
    "borderBottom": "1px solid #f0f0f0",
    "padding": "16px 24px",
}


def render_asset_allocation_chart() -> fac.AntdCard:
    """渲染资产配置饼图"""
    return fac.AntdCard(
        title="资产配置",
        bordered=False,
        children=[
            dcc.Graph(
                id="asset-allocation-pie",
                style={
                    "height": "360px",
                },
                config={
                    "displayModeBar": False,
                },
            )
        ],
        style={**CARD_STYLES, ":hover": CARD_HOVER_STYLES},
        headStyle={
            "borderBottom": "1px solid #f0f0f0",
            "padding": "16px 24px",
        },
    )


def render_performance_chart() -> fac.AntdCard:
    """渲染收益走势图"""
    return fac.AntdCard(
        title="收益走势",
        bordered=False,
        children=[
            dcc.Graph(
                id="performance-line",
                style={
                    "height": "360px",
                },
                config={
                    "displayModeBar": False,
                },
            )
        ],
        style={**CARD_STYLES, ":hover": CARD_HOVER_STYLES},
        headStyle={
            "borderBottom": "1px solid #f0f0f0",
            "padding": "16px 24px",
        },
    )
