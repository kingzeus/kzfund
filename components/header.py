import dash
from dash import html
import feffery_antd_components as fac


def create_header():
    return fac.AntdRow(
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
                        fac.AntdButton("数据导入", type="primary", id="upload-button"),
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
    )
