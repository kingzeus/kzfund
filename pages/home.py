from typing import Dict, Any, List, Optional, Tuple
from dash import dcc, html, callback, Output, Input, State, no_update
import feffery_antd_components as fac
from models.database import get_statistics


def render_home_page() -> html.Div:
    """渲染首页"""
    # 获取初始统计数据
    initial_stats = get_statistics()

    return html.Div(
        [
            # Store 组件用于存储统计数据
            dcc.Store(id="statistics-store", data=initial_stats),
            # 页面标题
            fac.AntdRow(
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdIcon(
                                icon="HomeOutlined",
                                style={"fontSize": "24px", "marginRight": "8px"},
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
                        fac.AntdCard(
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
                            style={
                                "height": "100%",
                                "borderRadius": "12px",
                                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.08)",
                                "transition": "all 0.3s ease",
                                "background": "linear-gradient(to bottom, #ffffff, #fafafa)",
                                ":hover": {
                                    "boxShadow": "0 4px 16px rgba(24, 144, 255, 0.12)",
                                    "transform": "translateY(-2px)",
                                },
                            },
                            headStyle={
                                "borderBottom": "none",
                                "padding": "16px 24px 0 24px",
                                "fontSize": "16px",
                                "fontWeight": "500",
                                "color": "#262626",
                                "textAlign": "center",
                            },
                        ),
                        span=6,
                        style={
                            "padding": "12px",
                        },
                    ),
                    fac.AntdCol(
                        fac.AntdCard(
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
                            style={
                                "height": "100%",
                                "borderRadius": "4px",
                                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.09)",
                            },
                        ),
                        span=6,
                        style={"padding": "8px"},
                    ),
                    fac.AntdCol(
                        fac.AntdCard(
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
                            style={
                                "borderRadius": "12px",
                            },
                        ),
                        span=6,
                        style={"padding": "8px"},
                    ),
                    fac.AntdCol(
                        fac.AntdCard(
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
                            style={
                                "borderRadius": "12px",
                            },
                        ),
                        span=6,
                        style={"padding": "8px"},
                    ),
                ]
            ),
            # 图表区域
            fac.AntdRow(
                [
                    fac.AntdCol(
                        fac.AntdCard(
                            title="资产配置",
                            bordered=False,
                            children=[
                                html.Div(
                                    id="asset-allocation-pie",
                                    style={
                                        "height": "360px",
                                        "padding": "16px 0",
                                    },
                                )
                            ],
                            style={
                                "height": "100%",
                                "borderRadius": "8px",
                                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.08)",
                                "transition": "all 0.3s ease",
                                ":hover": {
                                    "boxShadow": "0 4px 16px rgba(0, 0, 0, 0.1)",
                                },
                            },
                            headStyle={
                                "borderBottom": "1px solid #f0f0f0",
                                "padding": "16px 24px",
                            },
                        ),
                        span=12,
                        style={"padding": "8px"},
                    ),
                    fac.AntdCol(
                        fac.AntdCard(
                            title="收益走势",
                            bordered=False,
                            children=[
                                html.Div(
                                    id="performance-line",
                                    style={
                                        "height": "360px",
                                        "padding": "16px 0",
                                    },
                                )
                            ],
                            style={
                                "height": "100%",
                                "borderRadius": "8px",
                                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.08)",
                                "transition": "all 0.3s ease",
                                ":hover": {
                                    "boxShadow": "0 4px 16px rgba(0, 0, 0, 0.1)",
                                },
                            },
                            headStyle={
                                "borderBottom": "1px solid #f0f0f0",
                                "padding": "16px 24px",
                            },
                        ),
                        span=12,
                        style={"padding": "8px"},
                    ),
                ]
            ),
        ],
        style={"padding": "24px"},
    )
