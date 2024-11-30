# 任务详情弹窗模块
# 1. Store组件
#    - task-detail-task-id: 存储正在查看的任务ID
# 提供任务详情查看功能:
# - 渲染任务详情弹窗
# - 处理详情查看操作


import logging
from collections import Counter

import feffery_antd_components as fac
from dash import Input, Output, State, callback, callback_context, dcc, html, no_update, set_props
from dash.development.base_component import Component
from dash.exceptions import PreventUpdate
from feffery_utils_components import FefferyJsonViewer

from config import PAGE_CONFIG
from models.database import get_record
from models.task import ModelTask
from pages.task.task_utils import (
    STATUS_COLORS,
    STATUS_LABELS,
    create_name_with_input_params,
    create_status_tag,
    get_sub_tasks,
)
from scheduler.job_manager import JobManager
from scheduler.tasks import TaskStatus
from utils.datetime_helper import format_datetime
from utils.string_helper import json_str_to_dict

logger = logging.getLogger(__name__)


def render_task_detail_modal() -> Component:
    """渲染任务详情对话框"""
    return fac.Fragment(
        [
            dcc.Store(id="task-detail-task-id", data=""),
            fac.AntdModal(
                id="task-detail-modal",
                title="任务详情",
                visible=False,
                width=1000,
                okText="关闭",
                cancelText=None,
                maskClosable=True,
                centered=True,
                children=[
                    # 添加30秒定时刷新组件
                    dcc.Interval(
                        id="task-detail-interval",
                        interval=PAGE_CONFIG["TASK_DETAIL_INTERVAL_TIME"],
                    ),
                    html.Div(id="task-detail-content"),  # 使用独立的内容容器
                ],
                bodyStyle={
                    "padding": "24px",
                    "maxHeight": "80vh",
                    "overflowY": "auto",
                },
            ),
        ]
    )


@callback(
    [
        Output("task-detail-modal", "visible"),
        Output("task-detail-content", "children", allow_duplicate=True),
        Output("task-detail-task-id", "data", allow_duplicate=True),
        Output("task-detail-interval", "disabled", allow_duplicate=True),
    ],
    [
        Input("task-list", "nClicksButton"),
        State("task-list", "clickedCustom"),
        State("task-list", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def handle_task_detail(nClicks, custom, recentlyButtonClickedRow):
    """处理任务详情查看"""
    ctx = callback_context
    if not ctx.triggered:
        raise PreventUpdate

    try:
        task_id = recentlyButtonClickedRow["task_id"]

        if custom != "view":
            return no_update

        task = get_record(ModelTask, {"task_id": task_id})
        if not task:
            logger.warning("未找到任务: %s", task_id)
            return no_update

        # 是否更新任务详情内容
        is_update = task.status == TaskStatus.RUNNING or task.status == TaskStatus.PENDING

        content = get_task_detail(task.to_dict())
        logger.info("显示任务详情: %s", task_id)
        return True, content, task_id, not is_update

    except Exception as e:
        logger.error("处理任务详情失败: %s", str(e), exc_info=True)
        return no_update


@callback(
    Output("task-detail-task-id", "data", allow_duplicate=True),
    Input("task-detail-modal", "visible"),
    prevent_initial_call=True,
)
def update_task_detail_task_id(visible: bool) -> str:
    """更新正在查看的任务ID"""
    if visible:
        return no_update
    else:
        return ""


# 添加回调函数
@callback(
    Output("message-container", "children", allow_duplicate=True),
    [
        Input("subtask-table", "nClicksButton"),
        State("subtask-table", "clickedCustom"),
        State("subtask-table", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def handle_sub_task_action(nClicks, custom, recentlyButtonClickedRow):
    """处理子任务操作的回调"""
    if not nClicks:
        raise PreventUpdate

    if custom == "view":
        # 关闭当前任务详情弹窗
        set_props("task-detail-modal", {"visible": False})
        return no_update
    elif custom == "copy":
        task_id = recentlyButtonClickedRow["task_id"]
        JobManager().copy_task(task_id)
        return fac.AntdMessage(content="任务重新运行", type="success")
    else:
        return no_update


def get_task_detail(task: dict) -> list:
    """获取任务详情内容

    Args:
        task_id: 任务ID

    Returns:
        list: 任务详情内容组件列表
    """

    try:
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
        subtasks = [sub_task.to_dict() for sub_task in get_sub_tasks(task["task_id"])]

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
                                "width": "6%",
                            },
                            {
                                "title": "任务ID",
                                "dataIndex": "task_id",
                                "key": "task_id",
                                "width": "20%",
                            },
                            {
                                "title": "任务名称",
                                "dataIndex": "name",
                                "key": "name",
                                "width": "10%",
                            },
                            {
                                "title": "状态",
                                "dataIndex": "status_tag",
                                "key": "status",
                                "width": "11%",
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
                                "width": "18%",
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
                                "name": create_name_with_input_params(subtask),
                                "status_tag": create_status_tag(subtask),
                                "progress_bar": fac.AntdProgress(
                                    percent=subtask["progress"],
                                    size="small",
                                ),
                                "start_time": (
                                    format_datetime(subtask["start_time"])
                                    if subtask.get("start_time")
                                    else ""
                                ),
                                "action": [
                                    {
                                        "icon": "antd-eye",
                                        "type": "link",
                                        "iconRenderer": "AntdIcon",
                                        "custom": "view",
                                    },
                                    {
                                        "icon": "antd-reload",
                                        "type": "link",
                                        "iconRenderer": "AntdIcon",
                                        "custom": "copy",
                                    },
                                ],
                            }
                            for i, subtask in enumerate(subtasks)
                        ],
                        bordered=True,
                        size="small",
                        pagination=False,
                    ),
                ]
            )

        return content

    except Exception as e:
        logger.error("获取任务详情失败: %s", str(e), exc_info=True)
        return []


# 修改定时更新回调
@callback(
    Output("task-detail-content", "children", allow_duplicate=True),
    Output("task-detail-interval", "disabled", allow_duplicate=True),
    [
        Input("task-detail-interval", "n_intervals"),
        State("task-detail-task-id", "data"),
    ],
    prevent_initial_call=True,
)
def update_task_detail(n: int, task_id: str) -> list:
    """定时更新任务详情

    Args:
        n: 定时器触发次数
        task_id: 当前查看的任务ID

    Returns:
        list: 更新后的任务详情内容
    """
    if not task_id or len(task_id) < 1:
        raise PreventUpdate

    task = get_record(ModelTask, {"task_id": task_id})
    if not task:
        raise PreventUpdate

    logger.info("定时更新任务详情: %s", task_id)
    is_update = task.status == TaskStatus.RUNNING or task.status == TaskStatus.PENDING

    return get_task_detail(task.to_dict()), not is_update
