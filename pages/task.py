from pprint import pprint
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import dash
from dash import html, dcc, Input, Output, State, callback, ALL, ClientsideFunction
import feffery_antd_components as fac
from dash.exceptions import PreventUpdate
import json
import uuid
import logging

from scheduler.job_manager import JobManager, TaskStatus
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
def process_task_data(task: Dict[str, Any]) -> Dict[str, Any]:
    """处理任务数据，添加UI所需的字段

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


def create_task(
    task_type: str,
    params: List[Dict[str, Any]],
    param_values: List[Any],
    priority: Optional[int] = None,
    timeout: Optional[int] = None,
) -> bool:
    """创建任务

    Args:
        task_type: 任务类型
        params: 参数配置列表
        param_values: 参数值列表
        priority: 优先级
        timeout: 超时时间

    Returns:
        是否创建成功
    """
    # 构建任务参数
    task_params = {}
    for param, value in zip(params, param_values):
        if param.get("required", False) and not value:
            logger.warning(f"缺少必需参数: {param['name']}")
            return False
        task_params[param["key"]] = value

    # 创建任务
    try:
        JobManager().add_task(
            task_type=task_type, priority=priority, timeout=timeout, **task_params
        )
        logger.info(f"创任务成功: {task_type}")
        return True
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}", exc_info=True)
        return False


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


def create_operation_buttons(task_id: str, status: str) -> fac.AntdSpace:
    """创建操作按钮

    Args:
        task_id: 任务ID
        status: 任务状态

    Returns:
        操作按钮组件
    """
    return fac.AntdSpace(
        [
            fac.AntdButton(
                fac.AntdIcon(icon="antd-eye"),
                type="link",
                id={
                    "type": "task-action",
                    "index": task_id,
                    "action": "view",
                },
            ),
            fac.AntdButton(
                fac.AntdIcon(
                    icon="antd-pause-circle"
                    if status == TaskStatus.RUNNING
                    else "antd-play-circle"
                ),
                type="link",
                id={
                    "type": "task-action",
                    "index": task_id,
                    "action": "pause" if status == TaskStatus.RUNNING else "resume",
                },
            )
            if status in [TaskStatus.RUNNING, TaskStatus.PAUSED]
            else None,
        ]
    )


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
    """渲染任务创建对话框"""
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
                    # 动态参数表单容器
                    html.Div(id="task-params-container"),
                    # 基础配置项
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
    """渲染务管理页面

    Returns:
        页面主容器件
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
            # 主要内区域
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
        Output("task-params-container", "children", allow_duplicate=True),
        Output("task-type-select", "value", allow_duplicate=True),
    ],
    [
        Input("add-task-btn", "nClicks"),
        Input("task-type-select", "value"),
    ],
    prevent_initial_call=True,
)
def show_task_modal(n_clicks, task_type):
    """显示任务创建对话框并更新参数表单

    Args:
        n_clicks: 按钮点击次数
        task_type: 任务类型

    Returns:
        对话框显示状态、参数表单组件列表和任务类型值
    """
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"]

    # 获取第一个可用的任务类型作为默认值
    default_task_type = next(iter(TaskFactory().get_task_types().keys()), None)

    if trigger_id == "add-task-btn.nClicks":
        if n_clicks:
            # 打开弹窗时，置默认任务类型并生成对应的参数表单
            if default_task_type:
                param_items = generate_param_items(default_task_type)
                return True, param_items, default_task_type
            return True, [], None

    elif trigger_id == "task-type-select.value":
        if not task_type:
            return dash.no_update, [], dash.no_update

        param_items = generate_param_items(task_type)
        return dash.no_update, param_items, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update


def generate_param_form_item(
    param: Dict[str, Any], use_pattern_id: bool = True
) -> fac.AntdFormItem:
    """生成参数表单项"""
    # 根据参数类型创建不同的输入组件
    if param["type"] == "fund-code-aio":
        # 使用 FundCodeAIO 组件的特定 ID 格式
        input_component = FundCodeAIO(aio_id=f"task-param-{param['key']}")
    else:
        # 其他类型的输入组件使用通用的 ID 格式
        if param["type"] == "string":
            input_component = fac.AntdInput(
                id={"type": "task-param", "param": param["key"]}
                if use_pattern_id
                else f"param-{param['key']}",
                placeholder=param.get("description", ""),
                style={"width": "100%"},
            )
        elif param["type"] == "number":
            input_component = fac.AntdInputNumber(
                id={"type": "task-param", "param": param["key"]}
                if use_pattern_id
                else f"param-{param['key']}",
                placeholder=param.get("description", ""),
                style={"width": "100%"},
            )
        elif param["type"] == "select":
            input_component = fac.AntdSelect(
                id={"type": "task-param", "param": param["key"]}
                if use_pattern_id
                else f"param-{param['key']}",
                options=param.get("options", []),
                placeholder=param.get("description", ""),
                style={"width": "100%"},
            )
        elif param["type"] == "date":
            input_component = fac.AntdDatePicker(
                id={"type": "task-param", "param": param["key"]}
                if use_pattern_id
                else f"param-{param['key']}",
                placeholder=param.get("description", ""),
                style={"width": "100%"},
            )
        else:
            logger.warning(f"未知的参数类型: {param['type']}")
            return None

    return fac.AntdFormItem(
        label=param["name"],
        required=param.get("required", False),
        tooltip=param.get("description", ""),
        children=input_component,
    )


def generate_param_items(task_type: str, use_pattern_id: bool = True) -> List[Any]:
    """生成任务参数表单项列表

    Args:
        task_type: 任务类型
        use_pattern_id: 是否使用模式匹配ID格式

    Returns:
        参数表单组件列表
    """
    # 获取任务类型配置
    task_config = TaskFactory().get_task_types().get(task_type, {})
    params = task_config.get("params", [])

    # 构建参数表单项
    param_items = []
    for param in params:
        form_item = generate_param_form_item(param, use_pattern_id)
        if form_item:
            param_items.append(form_item)

    return param_items


@callback(
    [
        Output("task-store", "data"),
        Output("task-modal", "visible", allow_duplicate=True),
        Output("task-type-select", "value", allow_duplicate=True),
        Output("priority-input", "value"),
        Output("timeout-input", "value"),
    ],
    Input("task-modal", "okCounts"),
    [
        State("task-type-select", "value"),
        State({"type": "task-param", "param": ALL}, "value"),  # 普通数
        # 添加 FundCodeAIO 的值获取
        State(
            FundCodeAIO.ids.select("task-param-fund_code"), "value"
        ),  # 直接获取基金代码值
        State("priority-input", "value"),
        State("timeout-input", "value"),
    ],
    prevent_initial_call=True,
)
def handle_task_create(
    ok_counts: int,
    task_type: str,
    param_values: List[Any],
    fund_code: Optional[str],
    priority: Optional[int],
    timeout: Optional[int],
) -> Tuple[List[Dict[str, Any]], bool, None, None, None]:
    """处理任务创建"""
    if not ok_counts or not task_type:
        raise PreventUpdate

    # 获取任务参数配置
    task_config = TaskFactory().get_task_types().get(task_type, {})
    params = task_config.get("params", [])

    # 构建参数字典
    task_params = {}
    param_index = 0

    for param in params:
        if param["type"] == "fund-code-aio":
            value = fund_code
        else:
            value = param_values[param_index]
            param_index += 1

        logger.debug(f"处理参数: {param['key']} = {value}")

        if param.get("required", False) and not value:
            logger.warning(f"缺少必需参数: {param['name']}")
            raise PreventUpdate

        task_params[param["key"]] = value

    # 创建任务
    try:
        JobManager().add_task(
            task_type=task_type, priority=priority, timeout=timeout, **task_params
        )
        logger.info(f"创建任务成功: {task_type}")
    except Exception as e:
        logger.error(f"创建任务失败: {str(e)}", exc_info=True)
        raise PreventUpdate

    # 更新任务列表并关闭对话框
    tasks = JobManager().get_task_history()
    for task in tasks:
        task["created_at"] = format_datetime(task["created_at"])
        task["operation"] = create_operation_buttons(task["task_id"], task["status"])

    return tasks, False, None, None, None


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
        logger.error(f"处理任务操作失败: {str(e)}", exc_info=True)

    return dash.no_update


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
    Output("task-params-container", "children"),
    Input("task-type-select", "value"),
)
def update_task_params(task_type: str):
    """根据任务类型更新参数表单"""
    if not task_type:
        return []

    return generate_param_items(task_type, use_pattern_id=True)



@callback(
    Output("task-refresh-interval", "disabled"),
    [Input("task-store", "data")],
)
def toggle_refresh_interval(tasks_data: List[Dict[str, Any]]) -> bool:
    """根据任务状态控制定时器

    Args:
        tasks_data: 任务列表数据

    Returns:
        是否禁用定时器
    """
    # 检查是否有正在运行的任务
    has_running_tasks = any(
        task["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING]
        for task in tasks_data
    )

    # 如果有运行中的任务，启用定时器；否则禁用
    return not has_running_tasks


@callback(
    Output("task-store", "data", allow_duplicate=True),
    Input("task-refresh-interval", "n_intervals"),
    State("task-store", "data"),
    prevent_initial_call=True,
)
def refresh_tasks(
    n_intervals: int, current_tasks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """定期刷新任务列表"""
    try:
        # 获取需要更新的任务ID列表（未完成的任务）
        unfinished_task_ids = [
            task["task_id"]
            for task in current_tasks
            if task["status"]
            in [TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.PAUSED]
        ]

        if not unfinished_task_ids:
            return dash.no_update

        # 获取最新进度
        latest_progress = JobManager().get_tasks_progress(unfinished_task_ids)

        # 每隔N次刷新才获取完整任务信息
        should_full_refresh = (n_intervals % 5) == 0  # 比如每5次刷新一次完整信息

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
        return updated_tasks

    except Exception as e:
        logger.error(f"刷新任务列表失败: {str(e)}", exc_info=True)
        return dash.no_update
