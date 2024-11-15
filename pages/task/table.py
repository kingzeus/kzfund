"""任务列表表格模块

提供任务列表的表格展示功能:
- 表格数据展示
- 表格操作按钮
- 数据刷新
"""

from typing import List, Dict, Any
import feffery_antd_components as fac
from dash import callback, Input, Output, State, dcc, ALL
from dash.exceptions import PreventUpdate
import dash
import json
import logging

from scheduler.job_manager import JobManager, TaskStatus
from .utils import TABLE_STYLES, process_task_data

logger = logging.getLogger(__name__)

def render_task_table(initial_data: List[Dict[str, Any]]) -> fac.AntdCard:
    """渲染任务表格

    Args:
        initial_data: 初始任务数据列表

    Returns:
        任务表格卡片组件
    """
    return fac.AntdCard(
        title="任务管理",
        bordered=False,
        extra=[
            fac.AntdButton(
                "新建任务",
                type="primary",
                icon=fac.AntdIcon(icon="antd-plus"),
                id="add-task-btn",
            ),
        ],
        children=[
            fac.AntdTable(
                id="task-list",
                columns=[
                    {
                        "title": "任务ID",
                        "dataIndex": "task_id",
                        "key": "task_id",
                        "width": "20%",
                        "copyable": True,
                    },
                    {
                        "title": "任务名称",
                        "dataIndex": "name",
                        "key": "name",
                        "width": "15%",
                    },
                    {
                        "title": "状态",
                        "dataIndex": "status_tag",
                        "key": "status",
                        "width": "10%",
                    },
                    {
                        "title": "进度",
                        "dataIndex": "progress_bar",
                        "key": "progress",
                        "width": "15%",
                    },
                    {
                        "title": "创建时间",
                        "dataIndex": "created_at",
                        "key": "created_at",
                        "width": "15%",
                    },
                    {
                        "title": "操作",
                        "dataIndex": "actions",
                        "key": "operation",
                        "width": "15%",
                    },
                ],
                data=[process_task_data(task) for task in initial_data],
                bordered=True,
                size="small",
                pagination={
                    "pageSize": 10,
                    "showSizeChanger": True,
                    "showQuickJumper": True,
                },
                style=TABLE_STYLES,
            ),
        ],
        bodyStyle={"padding": "12px"},
        style={"width": "100%"},
    )

@callback(
    Output("task-list", "data"),
    Input("task-store", "data"),
    prevent_initial_call=True,
)
def update_task_list(store_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """更新任务列表"""
    return [process_task_data(task) for task in store_data]

@callback(
    Output("task-store", "data", allow_duplicate=True),
    Input({"type": "task-action", "index": ALL, "action": ALL}, "nClicks"),
    State("task-list", "data"),
    prevent_initial_call=True,
)
def handle_task_action(action_clicks, current_data):
    """处理任务操作"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    try:
        button_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
        task_id = button_id["index"]
        action = button_id["action"]

        if action in ["pause", "resume"]:
            logger.info(f"执行任务{action}操作: {task_id}")
            if action == "pause":
                JobManager().pause_task(task_id)
            else:
                JobManager().resume_task(task_id)

            # 获取最新任务列表
            tasks = JobManager().get_task_history()
            return tasks

    except Exception as e:
        logger.error(f"处理任务操作失败: {str(e)}")

    return dash.no_update

@callback(
    Output("task-refresh-interval", "disabled"),
    [Input("task-store", "data")],
)
def toggle_refresh_interval(tasks_data: List[Dict[str, Any]]) -> bool:
    """根据任务状态控制定时器"""
    has_running_tasks = any(
        task["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING]
        for task in tasks_data
    )
    return not has_running_tasks

@callback(
    [
        Output("task-store", "data", allow_duplicate=True),
        Output("task-table-spin", "spinning", allow_duplicate=True),
        Output("task-loading-state", "data", allow_duplicate=True),
    ],
    Input("task-refresh-interval", "n_intervals"),
    State("task-store", "data"),
    prevent_initial_call=True,
)
def refresh_tasks(n_intervals: int, current_tasks: List[Dict[str, Any]]):
    """定期刷新任务列表"""
    if n_intervals is None:
        raise PreventUpdate

    try:
        # 获取需要更新的任务ID列表
        unfinished_task_ids = [
            task["task_id"]
            for task in current_tasks
            if task["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.PAUSED]
        ]

        if not unfinished_task_ids:
            return dash.no_update, False, False

        # 获取最新进度
        latest_progress = JobManager().get_tasks_progress(unfinished_task_ids)

        # 每隔N次刷新才获取完整任务信息
        should_full_refresh = (n_intervals % 5) == 0

        # 创建任务数据的深拷贝
        updated_tasks = current_tasks.copy()

        if should_full_refresh:
            # 获取最新的完整任务列表
            latest_tasks = JobManager().get_task_history()

            # 更新任务状态和其他信息
            for i, task in enumerate(updated_tasks):
                latest_task = next(
                    (t for t in latest_tasks if t["task_id"] == task["task_id"]), None
                )
                if latest_task:
                    # 保持当前进度，除非有更新的进度
                    current_progress = task.get("progress", 0)
                    new_progress = latest_progress.get(
                        task["task_id"], latest_task.get("progress", current_progress)
                    )
                    # 只在进度增加时更新
                    if new_progress > current_progress:
                        latest_task["progress"] = new_progress
                    else:
                        latest_task["progress"] = current_progress

                    updated_tasks[i] = latest_task
        else:
            # 只更新进度
            for i, task in enumerate(updated_tasks):
                if task["status"] == TaskStatus.RUNNING:
                    if task["task_id"] in latest_progress:
                        current_progress = task.get("progress", 0)
                        new_progress = latest_progress[task["task_id"]]
                        # 只在进度增加时更新
                        if new_progress > current_progress:
                            task["progress"] = new_progress

        logger.debug(
            f"{'完整' if should_full_refresh else '进度'}刷新任务列表，"
            f"更新了 {len(latest_progress)} 个任务的进度"
        )
        return updated_tasks, False, False

    except Exception as e:
        logger.error(f"刷新任务列表失败: {str(e)}")
        # 发生错误时，显示错误提示
        fac.AntdMessage.error(f"刷新任务列表失败: {str(e)}")
        return dash.no_update, False, False

@callback(
    Output("task-table-spin", "spinning"),
    Output("task-loading-state", "data"),
    Input("task-refresh-interval", "n_intervals"),
    prevent_initial_call=True,
)
def update_loading_state(n_intervals):
    """更新加载状态"""
    if n_intervals is None:
        raise PreventUpdate

    # 开始刷新时显示加载状态
    return True, True