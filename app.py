from typing import Any
import dash
from dash import html, callback, Input, Output
import feffery_antd_components as fac
from components.header import create_header
from components.sidebar import create_sidebar
from pages.account import render_account_page
from pages.home import render_home_page
from backend import register_blueprint
from models.database import init_database
from config import (
    APP_NAME,
    DEBUG,
    SERVER_CONFIG,
    THEME_CONFIG,
)
from pages.transaction import render_transaction_page

# 初始化Dash应用
app = dash.Dash(
    __name__,
    title=APP_NAME,
    compress=True,
    update_title=None,
    suppress_callback_exceptions=True,
)


server = register_blueprint(app.server)

# 初始化数据库
init_database()

# 使用主题配置
PRIMARY_COLOR = THEME_CONFIG["primary_color"]
SUCCESS_COLOR = THEME_CONFIG["success_color"]
WARNING_COLOR = THEME_CONFIG["warning_color"]
ERROR_COLOR = THEME_CONFIG["error_color"]
PAGE_PADDING = THEME_CONFIG["page_padding"]
CARD_SHADOW = THEME_CONFIG["card_shadow"]

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
                    children=render_home_page(),
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
        return render_home_page()
    elif current_key == "account":
        return render_account_page()
    elif current_key == "transaction":
        return render_transaction_page()
    else:
        # 其他页面返回空白内容
        return html.Div()


if __name__ == "__main__":
    app.run(
        debug=DEBUG,
        host=SERVER_CONFIG["host"],
        port=SERVER_CONFIG["port"],
    )
