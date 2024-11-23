import feffery_antd_components as fac
from dash import set_props


def show_message(
    message: str,
    display_type: str = "default",
    duration: int = 3,
    component_id: str = "message-container",
):
    """显示消息框

    Args:
        message: 消息内容
        type: 消息类型，可选值: success/error/info/warning/default
    """
    set_props(
        component_id,
        {"children": fac.AntdMessage(content=message, type=display_type, duration=duration)},
    )
