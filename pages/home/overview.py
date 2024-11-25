"""数据概览卡片模块

提供首页数据概览的卡片组件:
- 总资产卡片: 显示总资产和日收益
- 持仓基金数卡片: 显示基金总数和活跃基金数
- 总收益率卡片: 显示总收益率和收益率统计
- 账户数量卡片: 显示账户数和组合数
"""

from typing import Any, Dict

import feffery_antd_components as fac
from dash import html

from .utils import CARD_HEAD_STYLES, CARD_STYLES

# ============= 样式常量 =============
VALUE_STYLES = {
    "primary": {
        "color": "#1890ff",
        "fontSize": "36px",
        "fontWeight": "500",
        "marginBottom": "8px",
        "textAlign": "center",
        "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto",
    },
    "secondary": {
        "color": "#52c41a",
        "fontSize": "20px",
        "fontWeight": "500",
    },
    "label": {
        "fontSize": "14px",
        "color": "#8c8c8c",
        "marginRight": "8px",
    },
}

FLEX_CENTER_STYLES = {
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
}


def render_total_assets_card() -> fac.AntdCard:
    """渲染总资产卡片"""
    return fac.AntdCard(
        title="总资产",
        bordered=False,
        children=[
            html.Div(
                [
                    html.H2(
                        "¥ 0.00",
                        id="total-assets",
                        style={
                            "color": "#1890ff",
                            "fontSize": "36px",
                            "fontWeight": "500",
                            "marginBottom": "8px",
                            "textAlign": "center",
                            "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto",
                        },
                    ),
                    html.Div(
                        [
                            html.Span(
                                "日收益",
                                style={
                                    "fontSize": "14px",
                                    "color": "#8c8c8c",
                                    "marginRight": "8px",
                                },
                            ),
                            html.Span(
                                "¥ 0.00",
                                id="daily-return",
                                style={
                                    "fontSize": "20px",
                                    "color": "#52c41a",
                                    "fontWeight": "500",
                                },
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "justifyContent": "center",
                            "marginTop": "4px",
                        },
                    ),
                ],
                style={
                    "display": "flex",
                    "flexDirection": "column",
                    "alignItems": "center",
                    "padding": "16px 0",
                },
            )
        ],
        style=CARD_STYLES,
        headStyle=CARD_HEAD_STYLES,
    )


def render_fund_count_card() -> fac.AntdCard:
    """渲染持仓基金数卡片"""
    return fac.AntdCard(
        title="持仓基金数",
        bordered=False,
        children=[
            html.H2(
                "0",
                id="fund-count",
                style={
                    "color": "#1890ff",
                    "margin": "16px 0",
                },
            ),
            fac.AntdStatistic(
                title="活跃基金",
                value=0,
                valueStyle={"fontSize": "16px"},
            ),
        ],
        style=CARD_STYLES,
    )


def render_return_rate_card() -> fac.AntdCard:
    """渲染总收益率卡片"""
    return fac.AntdCard(
        fac.AntdRow(
            [
                fac.AntdCol(
                    html.H2(
                        "0.00%",
                        id="total-return-rate",
                        style={
                            "color": "#52c41a",
                            "margin": "16px 0",
                        },
                    ),
                    span=12,
                ),
                fac.AntdCol(
                    fac.AntdStatistic(
                        title="收益率",
                        value=0,
                        suffix="%",
                        precision=2,
                        valueStyle={"color": "#52c41a"},
                    ),
                    span=12,
                ),
            ],
            gutter=10,
            style={
                "width": "100%",
                "height": "70px",
            },
        ),
        title="总收益率",
        hoverable=True,
        style=CARD_STYLES,
    )


def render_account_count_card(initial_stats: Dict[str, Any]) -> fac.AntdCard:
    """渲染账户数量卡片"""
    return fac.AntdCard(
        fac.AntdRow(
            [
                fac.AntdCol(
                    html.H2(
                        str(initial_stats["account_count"]),
                        id="account-count",
                        style={
                            "color": "#1890ff",
                            "fontSize": "96px",
                            "margin": "-13px 15px",
                            "lineHeight": "1",
                        },
                    ),
                    span=12,
                ),
                fac.AntdCol(
                    fac.AntdStatistic(
                        title="组合数",
                        value=initial_stats["portfolio_count"],
                        valueStyle={"color": "#52c41a"},
                    ),
                    span=12,
                ),
            ],
            gutter=10,
            style={
                "width": "100%",
                "height": "70px",
            },
        ),
        title="账户数量",
        hoverable=True,
        style=CARD_STYLES,
    )


def render_fund_data_card(initial_stats: Dict[str, Any]) -> fac.AntdCard:
    """渲染基金数据卡片"""
    return fac.AntdCard(
        fac.AntdRow(
            [
                fac.AntdCol(
                    html.H2(
                        str(initial_stats["fund_count"]),
                        id="fund-count",
                        style={
                            "color": "#1890ff",
                            "fontSize": "96px",
                            "margin": "-13px 15px",
                            "lineHeight": "1",
                        },
                    ),
                    span=12,
                ),
                fac.AntdCol(
                    fac.AntdStatistic(
                        title="基金净值数",
                        titleTooltip="基金净值总记录数",
                        value=initial_stats["fund_nav_count"],
                        valueStyle={"color": "#52c41a"},
                    ),
                    span=12,
                ),
            ],
            gutter=10,
            style={
                "width": "100%",
                "height": "70px",
            },
        ),
        title="基金数据",
        hoverable=True,
        style=CARD_STYLES,
    )


def render_today_fund_card(initial_stats: Dict[str, Any]) -> fac.AntdCard:
    """渲染今日基金数据卡片"""
    return fac.AntdCard(
        fac.AntdRow(
            [
                fac.AntdCol(
                    html.Span(
                        str(initial_stats["fund_count"]),
                        id="today-fund-count",
                        style={
                            "color": "#1890ff",
                            "fontSize": "96px",
                            "fontWeight": "700",
                            "height": "96px",
                            "margin": "-13px 15px",
                            "lineHeight": "1",
                        },
                    ),
                    # html.Span(
                    #     [
                    #         html.Span(
                    #             f"{initial_stats['today_fund_nav_count']}",
                    #             id="today-fund-count",
                    #             style={
                    #                 "color": "#1890ff",
                    #                 "fontSize": "96px",
                    #                 "margin": "-13px 15px",
                    #                 "lineHeight": "1",
                    #             },
                    #         ),
                    #         html.Span(
                    #             f"/{initial_stats['fund_count']}",
                    #             id="today-fund-count",
                    #             style={
                    #                 "color": "#1890ff",
                    #             },
                    #         ),
                    #     ]
                    # ),
                    span=12,
                ),
                fac.AntdCol(
                    fac.AntdStatistic(
                        title="基金净值更新",
                        titleTooltip="今天更新的基金净值数量",
                        value=initial_stats["today_update_fund_nav_count"],
                        valueStyle={"color": "#52c41a"},
                    ),
                    span=12,
                ),
            ],
            gutter=10,
            style={
                "width": "100%",
                "height": "70px",
            },
        ),
        title="今日更新基金",
        hoverable=True,
        style=CARD_STYLES,
    )
