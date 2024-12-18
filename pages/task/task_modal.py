"""任务创建弹窗模块

提供任务创建和编辑功能:
- 渲染任务创建弹窗
- 处理任务参数表单
- 处理任务创建和编辑操作
"""

import logging
from typing import Any, Dict, List, Optional

import dash
import feffery_antd_components as fac
from dash import ALL, Input, Output, State, callback, html
from dash.exceptions import PreventUpdate

from components.fund_code_aio import FundCodeAIO
from pages.task.task_utils import get_tasks
from scheduler.job_manager import JobManager
from scheduler.tasks import TaskFactory

logger = logging.getLogger(__name__)


def render_task_modal() -> fac.AntdModal:
    """渲染任务创建对话框"""
    return fac.AntdModal(
        id="task-modal",
        title="新建任务",
        visible=False,
        maskClosable=False,
        width=700,
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
                                for task_type, config in TaskFactory().get_task_types().items()
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
                        label="延迟时间",
                        tooltip="任务延迟执行的时间(秒)",
                        children=fac.AntdInputNumber(
                            id="delay-input",
                            placeholder="请输入延迟时间(秒)",
                            min=0,
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
                defaultValue=param.get("default", None),
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
                options=param.get("select_options", []),
                defaultValue=param.get("default", None),
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
        elif param["type"] == "boolean":
            input_component = fac.AntdSwitch(
                id=(
                    {"type": "task-param", "param": param["key"]}
                    if use_pattern_id
                    else f"param-{param['key']}"
                ),
                checkedChildren=fac.AntdIcon(icon="antd-check"),
                unCheckedChildren=fac.AntdIcon(icon="antd-close"),
                checked=True if param.get("default", False) else False,
            )
        else:
            logger.warning("未知的参数类型: %s", param["type"])
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
        Output("delay-input", "value"),
        Output("timeout-input", "value"),
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
    task_factory = TaskFactory()

    # 获取第一个可用的任务类型作为默认值
    default_task_type = next(iter(task_factory.get_task_types().keys()), None)

    if trigger_id == "add-task-btn.nClicks":
        if n_clicks:
            # 打开弹窗时，置默认任务类型并生成对应的参数表单
            if default_task_type:
                task_config = task_factory.get_task_types().get(default_task_type, {})
                param_items = generate_param_items(default_task_type)
                return (
                    True,
                    param_items,
                    default_task_type,
                    task_config.get("delay", 0),
                    task_config.get("timeout"),
                )
            return True, [], None, None, None

    elif trigger_id == "task-type-select.value":
        if not task_type:
            return dash.no_update, [], dash.no_update, None, None

        task_config = task_factory.get_task_types().get(task_type, {})
        param_items = generate_param_items(task_type)
        return (
            dash.no_update,
            param_items,
            dash.no_update,
            task_config.get("delay", 0),
            task_config.get("timeout"),
        )

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update


@callback(
    [
        Output("task-modal", "visible", allow_duplicate=True),
        Output("task-type-select", "value", allow_duplicate=True),
        Output("delay-input", "value", allow_duplicate=True),
        Output("timeout-input", "value", allow_duplicate=True),
        Output("task-list-interval", "disabled", allow_duplicate=True),
    ],
    Input("task-modal", "okCounts"),
    [
        State("task-type-select", "value"),
        State({"type": "task-param", "param": ALL}, "value"),
        State({"type": "task-param", "param": ALL}, "checked"),
        State({"aio_id": ALL, "component": "FundCodeAIO", "subcomponent": "select"}, "value"),
        State("delay-input", "value"),
        State("timeout-input", "value"),
    ],
    prevent_initial_call=True,
)
def handle_task_create(
    ok_counts: int,
    task_type: str,
    param_values: List[Any],
    param_checked: List[bool],
    fund_code_values: List[str],
    delay: Optional[int],
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
    fund_code_index = 0

    for param in params:
        if param["type"] == "fund-code-aio":
            value = fund_code_values[fund_code_index] if fund_code_values else None
            fund_code_index += 1
        elif param["type"] == "boolean":
            value = param_checked[param_index]
            param_index += 1
        else:
            value = param_values[param_index]
            param_index += 1

        logger.debug("处理参数: %s = %s", param["key"], value)

        if param.get("required", False) and not value:
            logger.warning("缺少必需参数: %s", param["name"])
            raise PreventUpdate

        task_params[param["key"]] = value

    # 创建任务
    try:
        JobManager().add_task(task_type=task_type, delay=delay, timeout=timeout, **task_params)
        logger.info("创建任务成功: %s", task_type)
    except Exception as e:
        logger.error("创建任务失败: %s", str(e), exc_info=True)
        raise PreventUpdate from e

    # 关闭对话框并清空表单
    return False, None, None, None, False
