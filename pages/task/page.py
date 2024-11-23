# 任务管理页面主渲染模块
#
# 页面结构:
# 1. Store组件
#    - task-store: 存储任务数据
#    - viewing-task-id: 存储正在查看的任务ID
#    - task-loading-state: 存储任务加载状态
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

from pages.task.detail_modal import render_task_detail_modal
from pages.task.modal import render_task_modal
from pages.task.table import render_task_table
from pages.task.utils import ICON_STYLES, PAGE_PADDING
from scheduler.job_manager import JobManager


def render_task_page() -> html.Div:
    """渲染任务管理页面

    Returns:
        包含完整页面结构的Div组件
    """
    tasks = JobManager().get_task_history()
    initial_tasks = [task.to_dict() for task in tasks]

    return html.Div(
        [
            # Store 组件
            dcc.Store(id="task-store", data=initial_tasks),
            dcc.Store(id="viewing-task-id", data=""),
            dcc.Store(id="task-loading-state", data=False),
            # 添加定时器组件
            dcc.Interval(
                id="task-refresh-interval",
                interval=500,  # 每500毫秒刷新一次
                disabled=True,  # 默认禁用
            ),
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
                            fac.AntdSpin(
                                render_task_table(initial_tasks),
                                id="task-table-spin",
                                spinning=False,  # 初始状态不显示加载
                            ),
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
