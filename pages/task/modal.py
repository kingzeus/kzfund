"""任务创建弹窗模块

提供任务创建和编辑功能:
- 渲染任务创建弹窗
- 处理任务参数表单
- 处理任务创建和编辑操作
"""

from typing import List, Dict, Any, Optional
import dash
from dash import html, Input, Output, State, callback, ALL
from dash.exceptions import PreventUpdate
import feffery_antd_components as fac
import logging

from scheduler.job_manager import JobManager
from scheduler.tasks import TaskFactory
from components.fund_code_aio import FundCodeAIO

logger = logging.getLogger(__name__)


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


def generate_param_form_item(
    param: Dict[str, Any], use_pattern_id: bool = True
) -> Optional[fac.AntdFormItem]:
    """生成参数表单项

    Args:
        param: 参数配置
        use_pattern_id: 是否使用模式匹配ID格式

    Returns:
        表单项组件
    """
    # 根据参数类型创建不同的输入组件
    if param["type"] == "fund-code-aio":
        input_component = FundCodeAIO(aio_id=f"task-param-{param['key']}")
    else:
        if param["type"] == "string":
            input_component = fac.AntdInput(
                id=(
                    {"type": "task-param", "param": param["key"]}
                    if use_pattern_id
                    else f"param-{param['key']}"
                ),
                placeholder=param.get("description", ""),
                style={"width": "100%"},
            )
        elif param["type"] == "number":
            input_component = fac.AntdInputNumber(
                id=(
                    {"type": "task-param", "param": param["key"]}
                    if use_pattern_id
                    else f"param-{param['key']}"
                ),
                placeholder=param.get("description", ""),
                style={"width": "100%"},
            )
        elif param["type"] == "select":
            input_component = fac.AntdSelect(
                id=(
                    {"type": "task-param", "param": param["key"]}
                    if use_pattern_id
                    else f"param-{param['key']}"
                ),
                options=param.get("options", []),
                placeholder=param.get("description", ""),
                style={"width": "100%"},
            )
        elif param["type"] == "date":
            input_component = fac.AntdDatePicker(
                id=(
                    {"type": "task-param", "param": param["key"]}
                    if use_pattern_id
                    else f"param-{param['key']}"
                ),
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
    task_config = TaskFactory().get_task_types().get(task_type, {})
    params = task_config.get("params", [])

    param_items = []
    for param in params:
        form_item = generate_param_form_item(param, use_pattern_id)
        if form_item:
            param_items.append(form_item)

    return param_items


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
    """显示任务创建对话框并更新参数表单"""
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
        State({"type": "task-param", "param": ALL}, "value"),
        State(FundCodeAIO.ids.select("task-param-fund_code"), "value"),
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
):
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
    return tasks, False, None, None, None
