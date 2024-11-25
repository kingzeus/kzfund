"""任务详情弹窗模块

提供任务详情查看功能:
- 渲染任务详情弹窗
- 处理详情查看操作
"""

import feffery_antd_components as fac
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from pages.task.task_utils import get_task_detail_items


def render_task_detail_modal() -> fac.AntdModal:
    """渲染任务详情对话框"""
    return fac.AntdModal(
        id="task-detail-modal",
        title="任务详情",
        visible=False,
        width=800,
        okText="关闭",
        cancelText=None,
        children=[
            fac.AntdDescriptions(
                id="task-detail-descriptions",
                items=[],
                bordered=True,
                column=2,
                size="small",
                labelStyle={"fontWeight": "bold"},
            )
        ],
    )


@callback(
    [
        Output("task-detail-modal", "visible"),
        Output("task-detail-descriptions", "items"),
        Output("viewing-task-id", "data"),
    ],
    [
        Input("task-list", "nClicksButton"),
    ],
    [
        State("task-list", "clickedCustom"),
        State("task-store", "data"),
    ],
    prevent_initial_call=True,
)
def handle_task_detail(n_clicks, custom_info, tasks_data):
    """处理任务详情查看"""
    if not n_clicks or not custom_info:
        raise PreventUpdate

    task_id = custom_info.get("id")
    action = custom_info.get("action")

    if action != "view":
        raise PreventUpdate

    task = next((t for t in tasks_data if t["task_id"] == task_id), None)
    if not task:
        raise PreventUpdate

    items = get_task_detail_items(task)
    return True, items, task_id
