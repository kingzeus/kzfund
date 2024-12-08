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
from feffery_utils_components import FefferyJsonViewer

from scheduler.job_manager import JobManager, TaskStatus
from utils.datetime_helper import format_datetime

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


# ============= 工具函数 =============
def get_task_store_data() -> List[Dict[str, Any]]:
    """获取任务store数据"""
    tasks = JobManager().get_task_history()
    return [task.to_dict() for task in tasks]


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
        "status_tag": fac.AntdTag(
            content=STATUS_LABELS.get(task["status"], "未知"),
            color=STATUS_COLORS.get(task["status"], "default"),
        ),
        "progress_bar": fac.AntdProgress(
            percent=task["progress"],
            size="small",
        ),
        "input_params": html.Div(
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
        else "-",
        "actions": create_operation_buttons(task),
    }


def create_operation_buttons(task: Dict[str, Any]) -> fac.AntdSpace:
    """创建操作按钮

    Args:
        task: 任务数据

    Returns:
        操作按钮组件
    """
    buttons = [
        fac.AntdButton(
            fac.AntdIcon(icon="antd-eye"),
            type="link",
            id={
                "type": "task-action",
                "index": task["task_id"],
                "action": "view",
            },
        ),
        fac.AntdButton(
            fac.AntdIcon(icon="antd-reload"),
            type="link",
            id={
                "type": "task-action",
                "index": task["task_id"],
                "action": "copy",
            },
        ),
    ]

    # 添加暂停/恢复按钮
    if task["status"] in [TaskStatus.RUNNING, TaskStatus.PAUSED]:
        buttons.append(
            fac.AntdButton(
                fac.AntdIcon(
                    icon=(
                        "antd-pause-circle"
                        if task["status"] == TaskStatus.RUNNING
                        else "antd-play-circle"
                    )
                ),
                type="link",
                id={
                    "type": "task-action",
                    "index": task["task_id"],
                    "action": ("pause" if task["status"] == TaskStatus.RUNNING else "resume"),
                },
            )
        )

    return fac.AntdSpace(buttons)


def get_task_detail_items(task: Dict[str, Any]) -> List[Dict[str, Any]]:
    """生成任务详情项

    Args:
        task: 任务数据

    Returns:
        详情项列表
    """
    return [
        {"label": "任务ID", "value": task["task_id"]},
        {"label": "任务名称", "value": task["name"]},
        {"label": "状态", "value": create_status_tag(task["status"])},
        {"label": "进度", "value": f"{task['progress']}%"},
        {"label": "优先级", "value": task["priority"]},
        {"label": "创建时间", "value": task["created_at"]},
        {
            "label": "开始时间",
            "value": format_datetime(task["start_time"]) if task["start_time"] else "-",
        },
        {
            "label": "结束时间",
            "value": format_datetime(task["end_time"]) if task["end_time"] else "-",
        },
        {"label": "执行结果", "value": task.get("result", "-")},
        {"label": "错误信息", "value": task.get("error", "-")},
    ]


def create_status_tag(status: str) -> Dict[str, str]:
    """创建状态标签配置

    Args:
        status: 任务状态

    Returns:
        包含标签文本和颜色的字典
    """
    return {
        "tag": STATUS_LABELS.get(status, "未知"),
        "color": STATUS_COLORS.get(status, "default"),
    }
