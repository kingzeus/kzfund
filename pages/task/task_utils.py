"""通用工具函数模块

包含:
- 任务状态常量
- 样式常量
- 工具函数
"""

import json
from typing import Any, Dict, List

import feffery_antd_components as fac
from dash import html
from dash.development.base_component import Component
from feffery_utils_components import FefferyJsonViewer

from kz_dash.models.database import get_record_count, get_record_list
from models.task import ModelTask
from scheduler.job_manager import JobManager, TaskStatus
from kz_dash.utility.datetime_helper import format_datetime

# ============= 状态常量 =============
STATUS_LABELS = {
    TaskStatus.PENDING: "等待中",
    TaskStatus.RUNNING: "运行中",
    TaskStatus.COMPLETED: "已完成",
    TaskStatus.FAILED: "失败",
    TaskStatus.PAUSED: "已暂停",
}

STATUS_COLORS = {
    TaskStatus.PENDING: "blue",
    TaskStatus.RUNNING: "processing",
    TaskStatus.COMPLETED: "success",
    TaskStatus.FAILED: "error",
    TaskStatus.PAUSED: "warning",
}

# ============= 样式常量 =============
PAGE_PADDING = 24
TABLE_STYLES = {"marginTop": "8px", "width": "100%"}
ICON_STYLES = {"fontSize": "24px", "marginRight": "8px"}

# ============= 任务常量 =============
TASK_PAGE_SIZE = 100


# ============= 工具函数 =============
def get_tasks() -> List[ModelTask]:
    """获取任务列表"""
    return get_record_list(ModelTask, {"parent_task_id__null": True}, order_by=["-created_at"])


def get_sub_tasks(task_id: str) -> List[ModelTask]:
    """获取子任务列表"""
    return get_record_list(ModelTask, {"parent_task_id": task_id}, order_by=["-created_at"])


def get_tasks_with_pagination(
    page: int = 1, page_size: int = TASK_PAGE_SIZE, filters: dict = None, sorter: dict = None
) -> Dict[str, Any]:
    """获取分页任务列表

    Args:
        page: 当前页码
        page_size: 每页数量
        filters: 过滤条件
        sorter: 排序条件

    Returns:
        包含分页数据的字典:
        {
            'total': 总记录数,
            'data': 当前页数据列表
        }
    """
    # 计算偏移量
    offset = (page - 1) * page_size

    # 构建查询条件
    query = {"parent_task_id__null": True}
    # if filters:
    #     # 处理状态过滤
    #     status_filter = filters.get("status")
    #     if status_filter:
    #         query["status__in"] = status_filter

    # 构建排序条件
    order_by = ["-created_at"]  # 默认按创建时间倒序
    if sorter:
        field = sorter.get("field")
        order = sorter.get("order")
        if field and order:
            # 处理特殊字段
            if field == "task_id":
                field = "id"
            order_by = [f"{'-' if order == 'descend' else ''}{field}"]

    # 获取总记录数
    total = get_record_count(ModelTask, query)

    # 获取分页数据
    tasks = get_record_list(
        ModelTask, search_fields=query, order_by=order_by, offset=offset, limit=page_size
    )

    return {"total": total, "data": [task.to_dict() for task in tasks]}


def prepare_task_for_display(task: Dict[str, Any]) -> Dict[str, Any]:
    """将基础任务字典转换为包含UI组件的显示数据

    此函数接收由convert_tasks_to_dict生成的基础字典，添加用于显示的UI组件，主要用于：
    1. 添加状态标签组件(AntdTag)
    2. 添加进度条组件(AntdProgress)
    3. 添加操作按钮组件
    4. 格式化日期时间

    Args:
        task: 基础任务字典

    Returns:
        包含UI组件的显示数据字典
    """
    # 处理输入参数
    input_params = task.get("input_params", None)
    if input_params:
        try:
            if isinstance(input_params, str):
                input_params = json.loads(input_params)
        except json.JSONDecodeError:
            input_params = {"error": "无法解析的参数"}

    return {
        **task,
        "created_at": format_datetime(task["created_at"]) if task["created_at"] else "-",
        "status_tag": create_status_tag(task),
        "progress_bar": fac.AntdProgress(
            percent=task["progress"],
            size="small",
        ),
        "input_params": (
            html.Div(
                [
                    FefferyJsonViewer(
                        data=input_params,
                        quotesOnKeys=False,
                        enableClipboard=False,
                        displayDataTypes=False,
                        displayObjectSize=False,
                        style={
                            "fontSize": "12px",
                            "backgroundColor": "transparent",
                            "padding": "0",
                            "textAlign": "left",
                        },
                        collapseStringsAfterLength=False,
                    ),
                ],
                style={
                    "maxHeight": "200px",
                    "overflow": "auto",
                    "textAlign": "left",
                    "padding": "4px",
                },
            )
            if input_params
            else "-"
        ),
        "actions": [
            {"icon": "antd-eye", "type": "link", "iconRenderer": "AntdIcon", "custom": "view"},
            {
                "icon": "antd-close",
                "type": "link",
                "danger": True,
                "iconRenderer": "AntdIcon",
                "custom": "delete",
            },
            {
                "icon": "antd-reload",
                "type": "link",
                "iconRenderer": "AntdIcon",
                "custom": "copy",
            },
        ],
    }


# def create_operation_buttons(task: Dict[str, Any]) -> fac.AntdSpace:
#     """创建操作按钮

#     Args:
#         task: 任务数据

#     Returns:
#         操作按钮组件
#     """
#     buttons = [
#         fac.AntdButton(
#             fac.AntdIcon(icon="antd-eye"),
#             type="link",
#             id={
#                 "type": "task-action",
#                 "index": task["task_id"],
#                 "action": "view",
#             },
#         ),
#         fac.AntdButton(
#             fac.AntdIcon(icon="antd-reload"),
#             type="link",
#             id={
#                 "type": "task-action",
#                 "index": task["task_id"],
#                 "action": "copy",
#             },
#         ),
#     ]

#     # 添加暂停/恢复按钮
#     if task["status"] in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
#         buttons.append(
#             fac.AntdButton(
#                 fac.AntdIcon(
#                     icon=(
#                         "antd-pause-circle"
#                         if task["status"] == TaskStatus.RUNNING
#                         else "antd-play-circle"
#                     )
#                 ),
#                 type="link",
#                 id={
#                     "type": "task-action",
#                     "index": task["task_id"],
#                     "action": ("pause" if task["status"] == TaskStatus.RUNNING else "resume"),
#                 },
#             )
#         )

#     return fac.AntdSpace(buttons)


def create_status_tag(task: dict, show_error: bool = True) -> Component:
    """创建状态标签配置"""
    if show_error and task["status"] == TaskStatus.FAILED:
        return fac.AntdTooltip(
            fac.AntdTag(
                content="失败",
                color="error",
            ),
            title=task.get("error") or "未知错误",
        )
    else:
        return fac.AntdTag(
            content=STATUS_LABELS.get(task["status"], "未知"),
            color=STATUS_COLORS.get(task["status"], "default"),
        )


def create_name_with_input_params(task: dict) -> Component:
    """创建任务名称和输入参数"""
    return fac.AntdPopover(
        task["name"],
        title="输入参数",
        content=(
            (
                html.Div(
                    [
                        FefferyJsonViewer(
                            data=json.loads(task["input_params"]),
                            quotesOnKeys=False,
                            enableClipboard=False,
                            displayDataTypes=False,
                            displayObjectSize=False,
                            style={
                                "fontSize": "12px",
                                "backgroundColor": "transparent",
                                "padding": "0",
                                "textAlign": "left",
                            },
                            collapseStringsAfterLength=False,
                        ),
                    ],
                    style={
                        "maxHeight": "200px",
                        "overflow": "auto",
                        "textAlign": "left",
                        "padding": "4px",
                    },
                )
                if task["input_params"]
                else "-"
            ),
        ),
    )
