from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import dash
from dash import html, dcc, Input, Output, State, callback, ALL
import feffery_antd_components as fac
from dash.exceptions import PreventUpdate
import json
import uuid
import logging

from scheduler.jobs import JobManager, TaskStatus
from scheduler.tasks import TaskFactory

from utils.datetime import format_datetime
from components.fund_code_aio import FundCodeAIO


logger = logging.getLogger(__name__)


# ============= 类型定义 =============
# 将所有类型定义放在文件开头

# ============= 常量定义 =============
# 将所有常量定义集中放置

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
def create_status_tag(status: str) -> Dict[str, str]:
    """创建状态标签配置

    Args:
        status: 任务状态

    Returns:
        包含tag和color的字典
    """
    return {
        "tag": STATUS_LABELS.get(status, "未知"),
        "color": STATUS_COLORS.get(status, "default"),
    }


def create_operation_buttons(task_id: str, status: str) -> List[Dict[str, Any]]:
    """创建操作按钮配置"""
    buttons = []

    # 查看详情按钮
    buttons.append(
        {
            "icon": "antd-eye",
            "iconRenderer": "AntdIcon",
            "type": "link",
            "custom": {"id": task_id, "action": "view"},
        }
    )

    # 暂停/恢复按钮
    if status == TaskStatus.RUNNING:
        buttons.append(
            {
                "icon": "antd-pause-circle",
                "iconRenderer": "AntdIcon",
                "type": "link",
                "custom": {"id": task_id, "action": "pause"},
            }
        )
    elif status == TaskStatus.PAUSED:
        buttons.append(
            {
                "icon": "antd-play-circle",
                "iconRenderer": "AntdIcon",
                "type": "link",
                "custom": {"id": task_id, "action": "resume"},
            }
        )

    return buttons


# ============= 组件渲染函数 =============
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
                data=[
                    {
                        **task,
                        "status_tag": fac.AntdTag(
                            content={
                                TaskStatus.PENDING: "等待中",
                                TaskStatus.RUNNING: "运行中",
                                TaskStatus.COMPLETED: "已完成",
                                TaskStatus.FAILED: "失败",
                                TaskStatus.PAUSED: "已暂停",
                            }.get(task["status"], "未知"),
                            color={
                                TaskStatus.PENDING: "blue",
                                TaskStatus.RUNNING: "processing",
                                TaskStatus.COMPLETED: "success",
                                TaskStatus.FAILED: "error",
                                TaskStatus.PAUSED: "warning",
                            }.get(task["status"], "default"),
                        ),
                        "progress_bar": fac.AntdProgress(
                            percent=task["progress"],
                            size="small",
                        ),
                        "actions": fac.AntdSpace(
                            [
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
                                    fac.AntdIcon(
                                        icon="antd-pause-circle"
                                        if task["status"] == TaskStatus.RUNNING
                                        else "antd-play-circle"
                                    ),
                                    type="link",
                                    id={
                                        "type": "task-action",
                                        "index": task["task_id"],
                                        "action": "pause"
                                        if task["status"] == TaskStatus.RUNNING
                                        else "resume",
                                    },
                                )
                                if task["status"]
                                in [TaskStatus.RUNNING, TaskStatus.PAUSED]
                                else None,
                            ]
                        ),
                    }
                    for task in initial_data
                ],
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


def render_task_modal() -> fac.AntdModal:
    """渲染任务建对话框"""
    return fac.AntdModal(
        id="task-modal",
        title="新建任务",
        visible=False,
        maskClosable=False,
        width=500,
        renderFooter=True,
        okText="确定",
        cancelText="取消",
        bodyStyle={
            "padding": "24px 24px 0",
        },
        children=[
            fac.AntdForm(
                id="task-form",
                labelCol={"span": 6},
                wrapperCol={"span": 18},
                children=[
                    fac.AntdFormItem(
                        label="任务类型",
                        required=True,
                        children=fac.AntdSelect(
                            id="task-type-select",
                            placeholder="请选择任务类型",
                            options=[
                                {
                                    "label": f"{config['name']} - {config['description']}",
                                    "value": task_type,
                                }
                                for task_type, config in TaskFactory()
                                .get_task_types()
                                .items()
                            ],
                            style={
                                "width": "100%",
                            },
                        ),
                    ),
                    # 基金信息任务特有的输入项
                    fac.AntdFormItem(
                        label="基金代码",
                        id="fund-code-form-item",
                        style={"display": "none"},
                        children=fac.AntdInput(
                            id="fund-code-input",
                            placeholder="请输入基金代码",
                            allowClear=True,
                            style={"width": "100%"},
                        ),
                    ),
                    fac.AntdFormItem(
                        label="优先级",
                        tooltip="任务执行的优先级(0-10),数字越大优先级越高",
                        children=fac.AntdInputNumber(
                            id="priority-input",
                            placeholder="请输入优先级",
                            min=0,
                            max=10,
                            style={"width": "100%"},
                        ),
                    ),
                    fac.AntdFormItem(
                        label="超时时间",
                        tooltip="任务最大执行时间(秒)",
                        children=fac.AntdInputNumber(
                            id="timeout-input",
                            placeholder="请输入超时时间(秒)",
                            min=1,
                            style={"width": "100%"},
                        ),
                    ),
                ],
                style={
                    "width": "100%",
                },
            )
        ],
    )


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


# ============= 页面主渲染函数 =============
def render_task_page() -> html.Div:
    """渲染任务管理页面

    Returns:
        页面主容器组件
    """
    initial_tasks = JobManager().get_task_history()

    # 处理任务数据
    for task in initial_tasks:
        task["created_at"] = format_datetime(task["created_at"])
        task["operation"] = create_operation_buttons(task["task_id"], task["status"])

    return html.Div(
        [
            # Store 组件
            dcc.Store(id="task-store", data=initial_tasks),
            dcc.Store(id="viewing-task-id", data=""),
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
                fac.AntdCol(
                    render_task_table(initial_tasks),
                    span=24,
                    style={"padding": f"{PAGE_PADDING}px"},
                ),
            ),
            # 对话框组件
            render_task_modal(),
            render_task_detail_modal(),
        ],
        style={"padding": f"{PAGE_PADDING}px"},
    )


# ============= 回调函数 =============
@callback(
    [
        Output("task-modal", "visible"),
        Output("fund-code-form-item", "style"),
    ],
    [
        Input("add-task-btn", "nClicks"),
        Input("task-type-select", "value"),
    ],
    prevent_initial_call=True,
)
def show_task_modal(n_clicks, task_type):
    """显示任务创建对话框

    Args:
        n_clicks: 按钮点击次数
        task_type: 任务类型

    Returns:
        对话框显示状态和表单项样式
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"]

    if trigger_id == "add-task-btn.nClicks":
        if n_clicks:
            return True, {"display": "none"}
    elif trigger_id == "task-type-select.value":
        # 如果选择了fund_info任务类型，显示基金代码输入框
        return dash.no_update, {
            "display": "block" if task_type == "fund_info" else "none"
        }

    return dash.no_update, dash.no_update


@callback(
    [
        Output("task-store", "data"),
        Output("task-modal", "visible", allow_duplicate=True),
        Output("task-type-select", "value"),
        Output("fund-code-input", "value"),
        Output("priority-input", "value"),
        Output("timeout-input", "value"),
    ],
    Input("task-modal", "okCounts"),
    [
        State("task-type-select", "value"),
        State("fund-code-input", "value"),
        State("priority-input", "value"),
        State("timeout-input", "value"),
    ],
    prevent_initial_call=True,
)
def handle_task_create(
    ok_counts: int,
    task_type: str,
    fund_code: Optional[str],
    priority: Optional[int],
    timeout: Optional[int],
) -> Tuple[List[Dict[str, Any]], bool, None, str, None, None]:
    """处理任务创建

    Args:
        ok_counts: 确认按钮点击次数
        task_type: 任务类型
        fund_code: 基金代码(可选)
        priority: 优先级(可选)
        timeout: 超时时间(可选)

    Returns:
        包含以下内容的元组:
        - tasks: 更新后的任务列表
        - visible: 对话框可见性
        - task_type: 任务类型选择值
        - fund_code: 基金代码输入值
        - priority: 优先级输入值
        - timeout: 超时时间输入值

    Raises:
        PreventUpdate: 当输入验证失败时
    """
    if not ok_counts or not task_type:
        raise PreventUpdate

    # 检查必要参数
    if task_type == "fund_info" and not fund_code:
        raise PreventUpdate

    # 准备任务参数
    params = {}
    if task_type == "fund_info":
        params["fund_code"] = fund_code

    # 创建任务
    JobManager().add_task(
        task_type=task_type, priority=priority, timeout=timeout, **params
    )

    # 更新任务列表并关闭对话框
    tasks = JobManager().get_task_history()
    for task in tasks:
        task["created_at"] = format_datetime(task["created_at"])
        task["operation"] = create_operation_buttons(task["task_id"], task["status"])

    return tasks, False, None, "", None, None


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

    items = [
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

    return True, items, task_id


@callback(
    Output("task-list", "data"),
    [
        Input("task-store", "data"),
        Input({"type": "task-action", "index": ALL, "action": ALL}, "nClicks"),
    ],
    [State("task-list", "data")],
    prevent_initial_call=True,
)
def update_task_list(store_data, action_clicks, current_data):
    """更新任务列表"""
    try:
        ctx = dash.callback_context
        if not ctx.triggered:
            raise PreventUpdate

        trigger = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger == "task-store":
            logger.debug("从store更新任务列表")
            # 处理数据
            return [
                {
                    **task,
                    "status_tag": fac.AntdTag(
                        content={
                            TaskStatus.PENDING: "等待中",
                            TaskStatus.RUNNING: "运行中",
                            TaskStatus.COMPLETED: "已完成",
                            TaskStatus.FAILED: "失败",
                            TaskStatus.PAUSED: "已暂停",
                        }.get(task["status"], "未知"),
                        color={
                            TaskStatus.PENDING: "blue",
                            TaskStatus.RUNNING: "processing",
                            TaskStatus.COMPLETED: "success",
                            TaskStatus.FAILED: "error",
                            TaskStatus.PAUSED: "warning",
                        }.get(task["status"], "default"),
                    ),
                    "progress_bar": fac.AntdProgress(
                        percent=task["progress"],
                        size="small",
                    ),
                    "actions": fac.AntdSpace(
                        [
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
                                fac.AntdIcon(
                                    icon="antd-pause-circle"
                                    if task["status"] == TaskStatus.RUNNING
                                    else "antd-play-circle"
                                ),
                                type="link",
                                id={
                                    "type": "task-action",
                                    "index": task["task_id"],
                                    "action": "pause"
                                    if task["status"] == TaskStatus.RUNNING
                                    else "resume",
                                },
                            )
                            if task["status"] in [TaskStatus.RUNNING, TaskStatus.PAUSED]
                            else None,
                        ]
                    ),
                }
                for task in store_data
            ]
        else:
            try:
                button_id = json.loads(trigger)
                task_id = button_id["index"]
                action = button_id["action"]

                if action in ["pause", "resume"]:
                    logger.info(f"执行任务{action}操作: {task_id}")
                    if action == "pause":
                        JobManager().pause_task(task_id)
                    else:
                        JobManager().resume_task(task_id)

                    # 获取最新任务列表并处理
                    tasks = JobManager().get_task_history()
                    logger.debug(f"更新任务列表，共{len(tasks)}个任务")
                    return [
                        {
                            **task,
                            "created_at": format_datetime(task["created_at"]),
                            "status_tag": fac.AntdTag(
                                content={
                                    TaskStatus.PENDING: "等待中",
                                    TaskStatus.RUNNING: "运行中",
                                    TaskStatus.COMPLETED: "已完成",
                                    TaskStatus.FAILED: "失败",
                                    TaskStatus.PAUSED: "已暂停",
                                }.get(task["status"], "未知"),
                                color={
                                    TaskStatus.PENDING: "blue",
                                    TaskStatus.RUNNING: "processing",
                                    TaskStatus.COMPLETED: "success",
                                    TaskStatus.FAILED: "error",
                                    TaskStatus.PAUSED: "warning",
                                }.get(task["status"], "default"),
                            ),
                            "progress_bar": fac.AntdProgress(
                                percent=task["progress"],
                                size="small",
                            ),
                            "actions": fac.AntdSpace(
                                [
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
                                        fac.AntdIcon(
                                            icon="antd-pause-circle"
                                            if task["status"] == TaskStatus.RUNNING
                                            else "antd-play-circle"
                                        ),
                                        type="link",
                                        id={
                                            "type": "task-action",
                                            "index": task["task_id"],
                                            "action": "pause"
                                            if task["status"] == TaskStatus.RUNNING
                                            else "resume",
                                        },
                                    )
                                    if task["status"]
                                    in [TaskStatus.RUNNING, TaskStatus.PAUSED]
                                    else None,
                                ]
                            ),
                        }
                        for task in tasks
                    ]

            except (json.JSONDecodeError, KeyError) as e:
                logger.error(f"处理任务操作失败: {str(e)}", exc_info=True)
                pass

        return dash.no_update

    except Exception as e:
        logger.error(f"更新任务列表失败: {str(e)}", exc_info=True)
        return dash.no_update  # 统一错误处理返回


def create_task_form():
    """创建任务表单"""
    factory = TaskFactory()
    task_types = factory.get_task_types()

    return html.Div(
        [
            fac.AntdForm(
                [
                    fac.AntdFormItem(
                        fac.AntdSelect(
                            id="task-type-select",
                            options=[
                                {"label": config["name"], "value": task_type}
                                for task_type, config in task_types.items()
                            ],
                            placeholder="请选择任务类型",
                        ),
                        label="任务类型",
                        required=True,
                    ),
                    # 动态参数表单区域
                    html.Div(id="task-params-container"),
                ]
            )
        ]
    )


@callback(
    Output("task-params-container", "children"), Input("task-type-select", "value")
)
def update_task_params(task_type: str):
    """根据任务类型更新参数表单"""
    if not task_type:
        return []

    factory = TaskFactory()
    task_config = factory.get_task_types()[task_type]

    param_items = []
    for param in task_config.get("params", []):
        if param["type"] == "string":
            input_component = fac.AntdInput(
                id=f"param-{param['key']}",
                placeholder=param["description"],
            )
        elif param["type"] == "number":
            input_component = fac.AntdInputNumber(
                id=f"param-{param['key']}",
                placeholder=param["description"],
            )
        elif param["type"] == "date":
            input_component = fac.AntdDatePicker(
                id=f"param-{param['key']}",
                placeholder=param["description"],
            )
        elif param["type"] == "select":
            input_component = fac.AntdSelect(
                id=f"param-{param['key']}",
                options=param["options"],
                placeholder=param["description"],
            )
        elif param["type"] == "fund-select":
            input_component = FundCodeAIO(
                id=f"param-{param['key']}",
                placeholder=param["description"],
            )

        param_items.append(
            fac.AntdFormItem(
                input_component,
                label=param["name"],
                required=param["required"],
            )
        )

    return param_items


@callback(
    Output("task-result", "children"),
    Input("submit-task", "nClicks"),
    [
        State("task-type-select", "value"),
        *[
            State(f"param-{param['key']}", "value")
            for task_type, config in TaskFactory().get_task_types().items()
            for param in config.get("params", [])
        ],
    ],
)
def submit_task(n_clicks, task_type, *param_values):
    """提交任务"""
    if not n_clicks or not task_type:
        return dash.no_update

    # 获取任务参数配置
    task_config = TaskFactory().get_task_types()[task_type]
    params = task_config.get("params", [])

    # 构建任务参数
    task_params = {}
    for param, value in zip(params, param_values):
        if param["required"] and not value:
            return f"请填写{param['name']}"
        task_params[param["key"]] = value

    # 提交任务
    task_id = str(uuid.uuid4())
    JobManager().submit_task(task_type, task_id, **task_params)

    return f"任务已提交: {task_id}"
