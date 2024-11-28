"""任务列表表格模块

提供任务列表的表格展示功能:
- 表格数据展示
- 表格操作按钮
- 数据刷新
"""

import json
import logging
from typing import Any, Dict, List

import dash
import feffery_antd_components as fac
from dash import ALL, Input, Output, State, callback, dcc, no_update
from dash.exceptions import PreventUpdate

from config import PAGE_CONFIG
from pages.task.task_utils import (
    STATUS_LABELS,
    TABLE_STYLES,
    TASK_PAGE_SIZE,
    get_tasks_with_pagination,
    prepare_task_for_display,
)
from scheduler.job_manager import JobManager, TaskStatus

logger = logging.getLogger(__name__)


def render_task_table() -> fac.AntdCard:
    """渲染任务表格

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
            # 添加定时器组件
            dcc.Interval(
                id="task-list-interval",
                interval=PAGE_CONFIG["TASK_LIST_INTERVAL_TIME"],
                disabled=True,  # 默认禁用
            ),
            fac.AntdTable(
                id="task-list",
                columns=[
                    {
                        "title": "任务ID",
                        "dataIndex": "task_id",
                        "key": "task_id",
                        "width": "15%",
                    },
                    {
                        "title": "任务名称",
                        "dataIndex": "name",
                        "key": "name",
                        "width": "10%",
                    },
                    {
                        "title": "输入参数",
                        "dataIndex": "input_params",
                        "key": "input_params",
                        "width": "20%",
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
                        "sorter": True,
                    },
                    {
                        "title": "操作",
                        "dataIndex": "actions",
                        "key": "actions",
                        "width": "10%",
                        "renderOptions": {
                            "renderType": "button",
                        },
                    },
                ],
                data=[],  # 初始为空，由回调函数加载数据
                bordered=True,
                size="small",
                pagination={
                    "pageSize": TASK_PAGE_SIZE,
                    "showSizeChanger": True,
                    "showQuickJumper": True,
                    "total": 0,  # 初始为0，由回调函数更新
                    "hideOnSinglePage": True,
                },
                mode="server-side",  # 使用服务端模式
                sortOptions={"sortDataIndexes": ["name", "created_at"]},
                # filterOptions={
                #     "status_tag": {
                #         "filterCustomItems": [
                #             {"label": label, "value": status}
                #             for status, label in STATUS_LABELS.items()
                #         ],
                #     }
                # },
                style=TABLE_STYLES,
            ),
        ],
        bodyStyle={"padding": "12px"},
        style={"width": "100%"},
    )


@callback(
    [
        Output("task-list", "data"),
        Output("task-list", "pagination"),
        Output("task-list-interval", "disabled", allow_duplicate=True),
    ],
    [
        Input("task-list", "pagination"),
        Input("task-list", "sorter"),
        Input("task-list", "filters"),
        Input("task-list-interval", "n_intervals"),
    ],
    prevent_initial_call=True,
)
def update_task_list(pagination, sorter, filters, n_intervals):
    """更新任务列表"""
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0] if ctx.triggered else None

    # 获取当前页码和每页数量
    current_page = pagination.get("current", 1) if pagination else 1
    page_size = pagination.get("pageSize", TASK_PAGE_SIZE) if pagination else TASK_PAGE_SIZE

    # 获取最新数据
    result = get_tasks_with_pagination(
        page=current_page,
        page_size=page_size,
        filters=filters,
        sorter=sorter,
    )

    # 准备显示数据
    display_data = [prepare_task_for_display(task) for task in result["data"]]

    # 更新分页信息
    pagination_info = {
        "current": current_page,
        "pageSize": page_size,
        "total": result["total"],
        "showSizeChanger": True,
        "showQuickJumper": True,
    }

    # 检查是否有运行中的任务
    has_running_tasks = any(
        task["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING] for task in result["data"]
    )

    return display_data, pagination_info, not has_running_tasks


# 添加回调函数
@callback(
    Output("message-container", "children", allow_duplicate=True),
    [
        Input("task-list", "nClicksButton"),
        State("task-list", "clickedCustom"),
        State("task-list", "recentlyButtonClickedRow"),
    ],
    prevent_initial_call=True,
)
def handle_task_list_action(nClicks, custom, recentlyButtonClickedRow):
    """处理任务列表操作的回调"""
    if not nClicks:
        raise PreventUpdate

    task_id = recentlyButtonClickedRow["task_id"]
    if custom == "view":
        # 查看任务详情，已单独处理
        return no_update
    elif custom == "copy":
        JobManager().copy_task(task_id)
        return fac.AntdMessage(content="任务重新运行", type="success")

    return no_update
