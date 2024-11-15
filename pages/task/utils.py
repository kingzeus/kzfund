"""通用工具函数模块

包含:
- 任务状态常量
- 样式常量
- 工具函数
"""

from typing import Dict, Any, List
import feffery_antd_components as fac
from scheduler.job_manager import TaskStatus
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
def process_task_data(task: Dict[str, Any]) -> Dict[str, Any]:
    """处理任务数据,添加UI所需的字段

    Args:
        task: 原始任务数据

    Returns:
        处理后的任务数据
    """
    return {
        **task,
        "created_at": format_datetime(task["created_at"]),
        "status_tag": fac.AntdTag(
            content=STATUS_LABELS.get(task["status"], "未知"),
            color=STATUS_COLORS.get(task["status"], "default"),
        ),
        "progress_bar": fac.AntdProgress(
            percent=task["progress"],
            size="small",
        ),
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
                    "action": (
                        "pause" if task["status"] == TaskStatus.RUNNING else "resume"
                    ),
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
