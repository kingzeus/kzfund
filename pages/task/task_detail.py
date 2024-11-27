"""任务详情弹窗模块

提供任务详情查看功能:
- 渲染任务详情弹窗
- 处理详情查看操作
"""

import json
import logging
from collections import Counter

import feffery_antd_components as fac
from dash import ALL, MATCH, Input, Output, State, callback, callback_context, html
from dash.exceptions import PreventUpdate
from feffery_utils_components import FefferyJsonViewer

from pages.task.task_utils import (
    STATUS_COLORS,
    STATUS_LABELS,
    create_status_tag,
    get_sub_tasks,
)
from scheduler.job_manager import JobManager
from scheduler.tasks import TaskStatus
from utils.datetime_helper import format_datetime
from utils.string_helper import json_str_to_dict

logger = logging.getLogger(__name__)


def render_task_detail_modal() -> fac.AntdModal:
    """渲染任务详情对话框"""
    return fac.AntdModal(
        id="task-detail-modal",
        title="任务详情",
        visible=False,
        width=1000,
        okText="关闭",
        cancelText=None,
        maskClosable=True,
        centered=True,
        children=html.Div(id="task-detail-content"),  # 使用独立的内容容器
        bodyStyle={
            "padding": "24px",
            "maxHeight": "80vh",
            "overflowY": "auto",
        },
    )


@callback(
    [
        Output("task-detail-modal", "visible"),
        Output("task-detail-content", "children"),  # 修改为更新content
        Output("viewing-task-id", "data"),
    ],
    [
        Input({"type": "task-action", "index": ALL, "action": ALL}, "nClicks"),
    ],
    [
        State("task-store", "data"),
    ],
    prevent_initial_call=True,
)
def handle_task_detail(action_clicks, tasks_data):
    """处理任务详情查看"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    try:
        button_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
        task_id = button_id["index"]
        action = button_id["action"]

        if action != "view":
            raise PreventUpdate

        task = next((t for t in tasks_data if t["task_id"] == task_id), None)
        if not task:
            logger.warning("未找到任务: %s", task_id)
            raise PreventUpdate

        # 构建详情内容
        content = [
            # 基本信息描述列表
            fac.AntdDescriptions(
                items=[
                    {"label": "任务ID", "children": task["task_id"]},
                    {"label": "任务名称", "children": task["name"]},
                    {
                        "label": "状态",
                        "children": create_status_tag(task, show_error=False),
                    },
                    {"label": "延迟执行", "children": f"{task['delay']}秒"},
                    {
                        "label": "进度",
                        "children": fac.AntdProgress(
                            percent=task["progress"],
                            size="small",
                        ),
                    },
                ],
                bordered=True,
                column=2,
                size="small",
                labelStyle={
                    "fontWeight": "bold",
                    "width": "100px",
                    "justifyContent": "flex-end",
                    "paddingRight": "8px",
                },
                style={"marginBottom": "24px"},
            ),
            fac.AntdDivider(children="时间信息", innerTextOrientation="left"),
            fac.AntdDescriptions(
                items=[
                    {"label": "创建时间", "children": format_datetime(task["created_at"])},
                    {"label": "更新时间", "children": format_datetime(task["updated_at"])},
                    {
                        "label": "开始时间",
                        "children": (
                            format_datetime(task["start_time"]) if task["start_time"] else "-"
                        ),
                    },
                    {
                        "label": "结束时间",
                        "children": format_datetime(task["end_time"]) if task["end_time"] else "-",
                    },
                ],
                bordered=True,
                column=2,
                size="small",
                labelStyle={
                    "fontWeight": "bold",
                    "width": "100px",
                    "justifyContent": "flex-end",
                    "paddingRight": "8px",
                },
                style={"marginBottom": "24px"},
            ),
            fac.AntdDivider(children="输入输出", innerTextOrientation="left"),
            fac.AntdDescriptions(
                items=[
                    {
                        "label": "输入参数",
                        "children": FefferyJsonViewer(
                            data=json_str_to_dict(task.get("input_params", "{}")),
                            quotesOnKeys=False,
                            enableClipboard=False,
                            displayDataTypes=False,
                            displayObjectSize=False,
                            style={
                                "fontSize": "12px",
                                "backgroundColor": "transparent",
                            },
                        ),
                        "span": 3,
                    },
                    {
                        "label": "执行结果",
                        "children": FefferyJsonViewer(
                            data=json_str_to_dict(task.get("result", "{}")),
                            quotesOnKeys=False,
                            enableClipboard=False,
                            displayDataTypes=False,
                            displayObjectSize=False,
                            style={
                                "fontSize": "12px",
                                "backgroundColor": "transparent",
                            },
                        ),
                        "span": 3,
                    },
                    {
                        "label": "错误信息",
                        "children": (
                            (task.get("error") or "未知错误")
                            if task["status"] == TaskStatus.FAILED
                            else "-"
                        ),
                        "span": 3,
                    },
                ],
                bordered=True,
                column=3,
                size="small",
                labelStyle={
                    "fontWeight": "bold",
                    "width": "80px",
                    "justifyContent": "flex-end",
                    "paddingRight": "8px",
                },
                style={"marginBottom": "24px"},
            ),
        ]

        # 添加子任务表格(如果有子任务)
        subtasks = [sub_task.to_dict() for sub_task in get_sub_tasks(task_id)]

        if subtasks:
            content.extend(
                [
                    fac.AntdDivider(children="子任务列表", innerTextOrientation="left"),
                    # 统计子任务各状态数量
                    fac.AntdSpace(
                        [
                            fac.AntdTag(
                                content=f"{STATUS_LABELS[status]}({count})",
                                color=STATUS_COLORS[status],
                            )
                            for status, count in Counter(
                                subtask["status"] for subtask in subtasks
                            ).items()
                        ],
                        style={
                            "marginBottom": "12px",
                            "display": "flex",
                            "justifyContent": "flex-start",
                        },
                    ),
                    fac.AntdTable(
                        id="subtask-table",
                        columns=[
                            {
                                "title": "序号",
                                "key": "index",
                                "dataIndex": "index",
                                "width": "8%",
                            },
                            {
                                "title": "任务ID",
                                "dataIndex": "task_id",
                                "key": "task_id",
                                "width": "20%",
                            },
                            {
                                "title": "状态",
                                "dataIndex": "status_tag",
                                "key": "status",
                                "width": "15%",
                            },
                            {
                                "title": "进度",
                                "dataIndex": "progress_bar",
                                "key": "progress",
                                "width": "15%",
                            },
                            {
                                "title": "开始时间",
                                "dataIndex": "start_time",
                                "key": "start_time",
                                "width": "16%",
                            },
                            {
                                "title": "结束时间",
                                "dataIndex": "end_time",
                                "key": "end_time",
                                "width": "16%",
                            },
                            {
                                "title": "操作",
                                "dataIndex": "action",
                                "key": "action",
                                "width": "5%",
                                "renderOptions": {
                                    "renderType": "button",
                                },
                            },
                        ],
                        data=[
                            {
                                "index": i + 1,
                                "task_id": subtask["task_id"],
                                "status_tag": create_status_tag(subtask),
                                "progress_bar": fac.AntdProgress(
                                    percent=subtask["progress"],
                                    size="small",
                                ),
                                "start_time": (
                                    format_datetime(subtask["start_time"])
                                    if subtask.get("start_time")
                                    else "-"
                                ),
                                "end_time": (
                                    format_datetime(subtask["end_time"])
                                    if subtask.get("end_time")
                                    else "-"
                                ),
                                "action": {
                                    "icon": "antd-reload",
                                    "type": "link",
                                    "iconRenderer": "AntdIcon",
                                },
                            }
                            for i, subtask in enumerate(subtasks)
                        ],
                        bordered=True,
                        size="small",
                        pagination=False,
                    ),
                ]
            )

        logger.info("显示任务详情: %s", task_id)
        return True, content, task_id

    except Exception as e:
        logger.error("处理任务详情失败: %s", str(e), exc_info=True)
        raise PreventUpdate


# 添加回调函数
@callback(
    Output("message-container", "children"),
    [
        Input("subtask-table", "nClicksButton"),
        State("subtask-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def handle_copy_task(nClicks, recentlyButtonClickedRow):
    """处理复制任务ID的回调"""
    if not nClicks:
        raise PreventUpdate

    task_id = recentlyButtonClickedRow["task_id"]
    JobManager().copy_task(task_id)
    return fac.AntdMessage(content="任务重新运行", type="success")
