from typing import Dict, Optional, Union, Any
from dash import html, Input, Output, callback, no_update
from dash.dependencies import Component
import feffery_antd_components as fac

# 定义类型别名
StyleDict = Dict[str, Union[str, int]]
MenuItemDict = Dict[str, Union[str, Dict[str, str]]]


def create_sidebar() -> html.Div:
    return html.Div(
        [
            html.Div(
                fac.AntdButton(
                    id="collapse-button",
                    icon=fac.AntdIcon(icon="antd-arrow-left"),
                    style={
                        "color": "#fff",
                        "border": "none",
                        "padding": "8px 16px",
                        "backgroundColor": "transparent",
                    },
                ),
                style={
                    "padding": "16px 8px",
                    "borderBottom": "1px solid rgba(255, 255, 255, 0.1)",
                    "textAlign": "right",
                },
            ),
            fac.AntdMenu(
                id="side-menu",
                menuItems=[
                    {
                        "component": "Item",
                        "props": {
                            "key": "portfolio",
                            "title": "持仓分析",
                            "icon": "antd-home",
                        },
                    },
                    {
                        "component": "Item",
                        "props": {
                            "key": "performance",
                            "title": "收益分析",
                            "icon": "antd-pie-chart",
                        },
                    },
                    {
                        "component": "Item",
                        "props": {
                            "key": "risk",
                            "title": "风险评估",
                            "icon": "antd-bell",
                        },
                    },
                ],
                mode="inline",
                defaultSelectedKey="portfolio",
                style={
                    "height": "calc(100% - 56px)",
                    "borderRight": "none",
                    "width": "100%",
                },
                theme="dark",
                inlineCollapsed=False,
            ),
        ],
        id="sidebar-container",
        style={
            "position": "fixed",
            "left": 0,
            "top": "64px",
            "bottom": 0,
            "backgroundColor": "#001529",
            "overflowY": "auto",
            "width": "200px",
            "transition": "all 0.2s",
            "zIndex": 100,
        },
    )


@callback(
    [
        Output("sidebar-container", "style"),
        Output("side-menu", "inlineCollapsed"),
        Output("collapse-button", "icon"),
    ],
    Input("collapse-button", "nClicks"),
    prevent_initial_call=True,
)
def toggle_sidebar(n_clicks: Optional[int]) -> tuple[StyleDict, bool, Any]:
    if n_clicks is None:
        return no_update

    is_collapsed = n_clicks % 2 == 1

    sidebar_style: StyleDict = {
        "position": "fixed",
        "left": 0,
        "top": "64px",
        "bottom": 0,
        "backgroundColor": "#001529",
        "overflowY": "auto",
        "width": "80px" if is_collapsed else "200px",
        "transition": "all 0.2s",
        "zIndex": 100,
    }

    return (
        sidebar_style,
        is_collapsed,
        fac.AntdIcon(icon="antd-arrow-right" if is_collapsed else "antd-arrow-left"),
    )
