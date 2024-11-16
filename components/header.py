from typing import Dict, Union

import feffery_antd_components as fac
from dash import html

# 定义类型别名
StyleDict = Dict[str, Union[str, int]]


def create_header() -> html.Div:
    return html.Div(
        fac.AntdRow(
            [
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdIcon(
                                icon="fc-data-sheet",
                                style={
                                    "fontSize": "30px",
                                    "color": "#fff",
                                    "marginRight": "8px",
                                },
                            ),
                            "基金持仓分析系统",
                        ],
                        style={
                            "color": "#fff",
                            "fontSize": "18px",
                            "fontWeight": "bold",
                            "display": "flex",
                            "alignItems": "center",
                        },
                    ),
                    span=16,
                ),
                fac.AntdCol(
                    fac.AntdSpace(
                        [
                            fac.AntdButton(
                                "数据导入",
                                type="primary",
                                id="upload-button",
                                icon=fac.AntdIcon(icon="fc-data-sheet"),
                            ),
                            fac.AntdButton(
                                "刷新数据",
                                id="refresh-button",
                                icon=fac.AntdIcon(icon="antd-reload"),
                                style={"color": "#fff", "borderColor": "#fff"},
                            ),
                        ],
                        style={
                            "height": "100%",
                            "display": "flex",
                            "alignItems": "center",
                        },
                    ),
                    span=8,
                    style={
                        "display": "flex",
                        "justifyContent": "flex-end",
                    },
                ),
            ],
            style={
                "height": "64px",
                "padding": "0 50px",
                "lineHeight": "64px",
            },
        ),
        style={
            "position": "fixed",
            "zIndex": 1,
            "width": "100%",
            "backgroundColor": "#001529",
        },
    )
