# 任务管理页面主渲染模块
#
# 页面结构:
#
# 2. 页面标题
#    - 图标 + 文字标题
#
# 3. 主要内容
#    - 任务列表表格
#
# 4. 弹窗组件
#    - 任务创建弹窗
#    - 任务详情弹窗
#


import feffery_antd_components as fac
from dash import dcc, html

from pages.task.task_detail import render_task_detail_modal
from pages.task.task_modal import render_task_modal
from pages.task.task_table import render_task_table
from pages.task.task_utils import ICON_STYLES, PAGE_PADDING


def render_task_page() -> html.Div:
    """渲染任务管理页面

    Returns:
        包含完整页面结构的Div组件
    """
    return html.Div(
        [
            # 页面标题
            fac.AntdRow(
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdIcon(
                                icon="antd-schedule",
                                style=ICON_STYLES,
                            ),
                            "任务管理",
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
            # 主要内容区域
            fac.AntdRow(
                [
                    fac.AntdCol(
                        [
                            render_task_table(),
                        ],
                        span=24,
                        style={"padding": f"{PAGE_PADDING}px"},
                    ),
                ]
            ),
            # 对话框组件
            render_task_modal(),
            render_task_detail_modal(),
        ],
        style={"padding": f"{PAGE_PADDING}px"},
    )
