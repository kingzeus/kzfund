from typing import Dict, Any
from dash import html
import feffery_antd_components as fac



def create_home_page() -> html.Div:
    """创建首页"""
    return html.Div(
        [
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
                                html.H2(
                                    "¥ 0.00",
                                    id="total-assets",
                                    style={
                                        "color": "#1890ff",
                                        "margin": "16px 0",
                                    },
                                ),
                                fac.AntdStatistic(
                                    title="日收益",
                                    value=0,
                                    precision=2,
                                    prefix="¥",
                                    valueStyle={"color": "#52c41a"},
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
                            title="总收益率",
                            bordered=False,
                            children=[
                                html.H2(
                                    "0.00%",
                                    id="total-return-rate",
                                    style={
                                        "color": "#52c41a",
                                        "margin": "16px 0",
                                    },
                                ),
                                fac.AntdStatistic(
                                    title="月收益率",
                                    value=0,
                                    suffix="%",
                                    precision=2,
                                    valueStyle={"color": "#52c41a"},
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
                            title="账户数",
                            bordered=False,
                            children=[
                                html.H2(
                                    "0",
                                    id="account-count",
                                    style={
                                        "color": "#1890ff",
                                        "margin": "16px 0",
                                    },
                                ),
                                fac.AntdStatistic(
                                    title="组合数",
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
                                    style={"height": "360px"},
                                )
                            ],
                            style={
                                "height": "100%",
                                "borderRadius": "4px",
                                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.09)",
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
                                    style={"height": "360px"},
                                )
                            ],
                            style={
                                "height": "100%",
                                "borderRadius": "4px",
                                "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.09)",
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
