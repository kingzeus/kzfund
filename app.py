import logging.config
import os
from typing import Any

import dash
import feffery_antd_components as fac
from dash import Input, Output, callback, html

from backend import register_blueprint
from components.header import create_header
from components.sidebar import create_sidebar
from config import APP_NAME, DEBUG, LOG_CONFIG, ROOT_DIR, SERVER_CONFIG, THEME_CONFIG
from data_source import init_data_source
from models.database import init_database
from pages.account import render_account_page
from pages.home import render_home_page
from pages.task import render_task_page
from pages.transaction import render_transaction_page


def init_log() -> logging.Logger:
    """初始化日志系统

    Returns:
        logging.Logger: 根日志记录器

    Raises:
        Exception: 日志系统初始化失败时抛出异常
    """
    # 确保日志目录存在
    log_dir = os.path.join(ROOT_DIR, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"创建日志目录: {log_dir}")

    # 初始化日志配置
    try:
        logging.config.dictConfig(LOG_CONFIG)
        logger = logging.getLogger(__name__)
        logger.info("日志系统初始化成功")
        return logger
    except Exception as e:
        print(f"日志系统初始化失败: {e}")
        raise


def init_application():
    """应用初始化"""
    # 初始化日志系统
    logger = init_log()

    # 初始化数据库
    init_database()
    logger.info("数据库初始化成功")

    # 初始化数据源
    init_data_source()
    logger.info("数据源初始化成功")


# 初始化Dash应用
app = dash.Dash(
    __name__,
    title=APP_NAME,
    compress=True,
    update_title=None,
    suppress_callback_exceptions=True,
    assets_folder="assets",
)


# 初始化数据库和数据源
init_application()

server = register_blueprint(app.server)

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
    elif current_key == "task":
        return render_task_page()
    else:
        # 其他页面返回空白内容
        return html.Div()


if __name__ == "__main__":
    app.run(
        debug=DEBUG,
        host=SERVER_CONFIG["host"],
        port=SERVER_CONFIG["port"],
    )
