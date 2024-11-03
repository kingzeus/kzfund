from typing import Any
import dash
from dash import html, callback, Input, Output
import feffery_antd_components as fac
from components.header import create_header
from components.sidebar import create_sidebar
from pages.account import create_account_page
from pages.home import create_home_page

# 初始化Dash应用
app = dash.Dash(
    __name__,
    title="基金持仓分析系统",
    update_title=None,
    suppress_callback_exceptions=True,
)
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
                    id="main-content",
                    children=create_home_page(),
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


# 添加内容区域响应侧边栏折叠的回调
@callback(
    Output("main-content", "style"),
    Input("side-menu", "inlineCollapsed"),
    prevent_initial_call=True,
)
def update_content_margin(is_collapsed: bool) -> dict:
    return {
        "padding": f"{PAGE_PADDING}px",
        "backgroundColor": "#f0f2f5",
        "minHeight": "calc(100vh - 64px)",
        "marginLeft": "80px" if is_collapsed else "200px",
        "marginTop": "64px",
        "transition": "margin-left 0.2s",
    }


# 添加页面内容回调
@callback(
    Output("main-content", "children"),
    Input("side-menu", "currentKey"),
    prevent_initial_call=False,
)
def update_page_content(current_key: str) -> Any:
    """根据菜单选择更新页面内容"""
    if current_key is None or current_key == "home":
        return create_home_page()
    elif current_key == "account":
        return create_account_page()
    # 其他页面返回空白内容
    return html.Div()


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
