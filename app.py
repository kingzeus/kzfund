from typing import Tuple
import dash
from dash import html, dcc, callback, Input, Output
import feffery_antd_components as fac
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.exceptions import PreventUpdate
from components.header import create_header
from components.sidebar import create_sidebar

# 初始化Dash应用
app = dash.Dash(__name__, title="基金持仓分析系统", update_title=None)
server = app.server

# 定义主题色和间距
PRIMARY_COLOR = "#1890ff"
SUCCESS_COLOR = "#52c41a"
WARNING_COLOR = "#faad14"
ERROR_COLOR = "#f5222d"
PAGE_PADDING = 24
CARD_SHADOW = "0 2px 8px rgba(0, 0, 0, 0.09)"

# 定义页面布局
app.layout = html.Div(
    [
        # 顶部导航栏
        create_header(),
        # 主要内容区域
        fac.AntdRow(
            [
                # 左侧菜单
                create_sidebar(),
                # 右侧内容区
                fac.AntdCol(
                    [
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
                                                    "color": PRIMARY_COLOR,
                                                    "margin": "16px 0",
                                                },
                                            ),
                                            fac.AntdStatistic(
                                                title="日收益",
                                                value=0,
                                                precision=2,
                                                prefix="¥",
                                                valueStyle={"color": SUCCESS_COLOR},
                                            ),
                                        ],
                                        style={
                                            "height": "100%",
                                            "borderRadius": "4px",
                                            "boxShadow": CARD_SHADOW,
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
                                                    "margin": "16px 0",
                                                    "color": PRIMARY_COLOR,
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
                                            "boxShadow": CARD_SHADOW,
                                        },
                                    ),
                                    span=6,
                                    style={"padding": "8px"},
                                ),
                            ],
                            style={"marginBottom": "24px"},
                        ),
                        # 图表区域
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdCard(
                                        title="资产配置",
                                        bordered=False,
                                        children=[
                                            dcc.Graph(
                                                id="asset-allocation-pie",
                                                style={
                                                    "height": "360px",
                                                    "padding": "12px 0",
                                                },
                                            )
                                        ],
                                        style={
                                            "height": "100%",
                                            "borderRadius": "4px",
                                            "boxShadow": CARD_SHADOW,
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
                                            dcc.Graph(
                                                id="performance-line",
                                                style={
                                                    "height": "360px",
                                                    "padding": "12px 0",
                                                },
                                            )
                                        ],
                                        style={
                                            "height": "100%",
                                            "borderRadius": "4px",
                                            "boxShadow": CARD_SHADOW,
                                        },
                                    ),
                                    span=12,
                                    style={"padding": "8px"},
                                ),
                            ],
                            style={"marginBottom": "24px"},
                        ),
                        # 基金列表
                        fac.AntdRow(
                            fac.AntdCol(
                                fac.AntdCard(
                                    title="基金持仓明细",
                                    bordered=False,
                                    children=[
                                        fac.AntdTable(
                                            id="fund-table",
                                            columns=[
                                                {
                                                    "title": "基金代码",
                                                    "dataIndex": "code",
                                                },
                                                {
                                                    "title": "���名称",
                                                    "dataIndex": "name",
                                                },
                                                {
                                                    "title": "持仓份额",
                                                    "dataIndex": "shares",
                                                },
                                                {
                                                    "title": "最新净值",
                                                    "dataIndex": "nav",
                                                },
                                                {
                                                    "title": "持仓市值",
                                                    "dataIndex": "market_value",
                                                },
                                                {
                                                    "title": "收益率",
                                                    "dataIndex": "return_rate",
                                                },
                                            ],
                                            data=[],
                                            style={"marginTop": "12px"},
                                        )
                                    ],
                                    style={
                                        "borderRadius": "4px",
                                        "boxShadow": CARD_SHADOW,
                                    },
                                ),
                                span=24,
                                style={"padding": "8px"},
                            )
                        ),
                    ],
                    id="main-content",
                    span=20,
                    style={
                        "padding": f"{PAGE_PADDING}px",
                        "backgroundColor": "#f0f2f5",
                        "minHeight": "calc(100vh - 64px)",
                        "marginLeft": "200px",
                        "marginTop": "64px",
                        "transition": "margin-left 0.2s",
                    },
                ),
            ],
            style={
                "position": "relative",
            },
        ),
    ],
    style={
        "backgroundColor": "#f0f2f5",
    },
)


# 回调函数示例
@callback(
    [Output("asset-allocation-pie", "figure"), Output("performance-line", "figure")],
    [Input("refresh-button", "nClicks")],
    prevent_initial_call=True,
)
def update_charts(n_clicks: int) -> Tuple[go.Figure, go.Figure]:
    if n_clicks is None:
        raise PreventUpdate

    try:
        # 示例数据 - 资产配置
        pie_data = pd.DataFrame(
            {
                "category": ["股票型", "债券型", "混合型", "货币型"],
                "value": [40, 30, 20, 10],
            }
        )

        pie_fig = px.pie(
            pie_data, values="value", names="category", title="资产配置比例"
        )
        pie_fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        # 示例数据 - 收益走势
        line_data = pd.DataFrame(
            {
                "date": pd.date_range(start="2023-01-01", periods=100),
                "value": range(100),
            }
        )

        line_fig = px.line(line_data, x="date", y="value", title="收益走势")
        line_fig.update_layout(xaxis_title="日期", yaxis_title="收益率(%)")

        return pie_fig, line_fig
    except Exception as e:
        print(f"Error in update_charts: {str(e)}")
        # 返回空白图表
        return go.Figure(), go.Figure()


# 添加内容区域响应侧边栏折叠的回调
@callback(
    Output("main-content", "style"),
    Input("side-menu", "inlineCollapsed"),
    prevent_initial_call=True,
)
def update_content_margin(is_collapsed):
    return {
        "padding": f"{PAGE_PADDING}px",
        "backgroundColor": "#f0f2f5",
        "minHeight": "calc(100vh - 64px)",
        "marginLeft": "80px" if is_collapsed else "200px",
        "marginTop": "64px",
        "transition": "margin-left 0.2s",
    }


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
