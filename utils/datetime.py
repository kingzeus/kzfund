from datetime import datetime
from typing import Union, Optional


def format_datetime(
    dt: Union[str, datetime, None],
    format: str = "%Y-%m-%d %H:%M",
    default: str = "未知时间",
) -> str:
    """
    统一的日期时间格式化函数

    Args:
        dt: 要格式化的日期时间，可以是datetime对象或ISO格式的字符串
        format: 输出格式，默认为 "%Y-%m-%d %H:%M"
        default: 当无法格式化时返回的默认值

    Returns:
        格式化后的时间字符串
    """
    if not dt:
        return default

    try:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        if isinstance(dt, datetime):
            return dt.strftime(format)
    except (ValueError, TypeError):
        pass

    return default


def get_timestamp() -> int:
    """获取当前时间戳"""
    return int(datetime.now().timestamp())
