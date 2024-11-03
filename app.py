from typing import Tuple
import dash
from dash import html, dcc, callback, Input, Output
import feffery_antd_components as fac
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from dash.exceptions import PreventUpdate

# 初始化Dash应用
app = dash.Dash(__name__, title="基金持仓分析系统", update_title=None)
server = app.server  # 添加server实例，用于生产环境部署

# 定义页面布局
app.layout = html.Div(
    [
        # 顶部导航栏
        fac.AntdRow(
            [
                fac.AntdCol(
                    fac.AntdPageHeader(
                        title="基金持仓分析系统",
                        ghost=False,
                    ),
                    span=18,
                ),
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdButton(
                                "数据导入", type="primary", id="upload-button"
                            ),
                            fac.AntdButton(
                                "刷新数据",
                                id="refresh-button",
                                style={"marginLeft": "8px"},
                            ),
                        ],
                        style={
                            "display": "flex",
                            "alignItems": "center",
                            "height": "100%",
                            "padding": "0 16px",
                        },
                    ),
                    span=6,
                ),
            ],
            style={"marginBottom": "20px"},
        ),
        # 主要内容区域
        fac.AntdRow(
            [
                # 左侧菜单
                fac.AntdCol(
                    fac.AntdMenu(
                        menuItems=[
                            {
                                "component": "Item",
                                "props": {
                                    "key": "portfolio",
                                    "title": "持仓分析",
                                    "icon": "fund",
                                },
                            },
                            {
                                "component": "Item",
                                "props": {
                                    "key": "performance",
                                    "title": "收益分析",
                                    "icon": "line-chart",
                                },
                            },
                            {
                                "component": "Item",
                                "props": {
                                    "key": "risk",
                                    "title": "风险评估",
                                    "icon": "warning",
                                },
                            },
                        ],
                        mode="inline",
                        style={"height": "100%"},
                    ),
                    span=4,
                    style={
                        "borderRight": "1px solid #f0f0f0",
                        "minHeight": "calc(100vh - 100px)",
                    },
                ),
                # 右侧内容区
                fac.AntdCol(
                    [
                        # 数据概览卡片
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdCard(
                                        title="总资产",
                                        bordered=True,
                                        children=[
                                            html.H2("¥ 0.00", id="total-assets"),
                                            fac.AntdStatistic(
                                                title="日收益",
                                                value=0,
                                                precision=2,
                                                prefix="¥",
                                                valueStyle={"color": "#3f8600"},
                                            ),
                                        ],
                                    ),
                                    span=6,
                                ),
                                fac.AntdCol(
                                    fac.AntdCard(
                                        title="持仓基金数",
                                        bordered=True,
                                        children=[
                                            html.H2("0", id="fund-count"),
                                            fac.AntdStatistic(
                                                title="活跃基金", value=0
                                            ),
                                        ],
                                    ),
                                    span=6,
                                ),
                            ],
                            gutter=16,
                            style={"marginBottom": "20px"},
                        ),
                        # 图表区域
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    fac.AntdCard(
                                        title="资产配置",
                                        bordered=True,
                                        children=[
                                            dcc.Graph(
                                                id="asset-allocation-pie",
                                                style={"height": "300px"},
                                            )
                                        ],
                                    ),
                                    span=12,
                                ),
                                fac.AntdCol(
                                    fac.AntdCard(
                                        title="收益走势",
                                        bordered=True,
                                        children=[
                                            dcc.Graph(
                                                id="performance-line",
                                                style={"height": "300px"},
                                            )
                                        ],
                                    ),
                                    span=12,
                                ),
                            ],
                            gutter=16,
                        ),
                        # 基金列表
                        fac.AntdRow(
                            fac.AntdCol(
                                fac.AntdCard(
                                    title="基金持仓明细",
                                    bordered=True,
                                    children=[
                                        fac.AntdTable(
                                            id="fund-table",
                                            columns=[
                                                {
                                                    "title": "基金代码",
                                                    "dataIndex": "code",
                                                },
                                                {
                                                    "title": "基金名称",
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
                                        )
                                    ],
                                ),
                                span=24,
                                style={"marginTop": "20px"},
                            )
                        ),
                    ],
                    span=20,
                    style={"padding": "20px"},
                ),
            ]
        ),
    ]
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


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
