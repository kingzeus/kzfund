from datetime import date, datetime
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


def format_date(
    dt: Union[str, date, None],
    output_format: str = "%Y-%m-%d",
    input_format: Optional[str] = None,
    default: str = "未知日期",
) -> str:
    """
    统一的日期格式化函数

    Args:
        dt: 要格式化的日期，可以是date对象、ISO格式字符串或指定格式的日期字符串
        output_format: 输出格式，默认为 "%Y-%m-%d"
        input_format: 输入日期字符串的格式，如果提供则使用strptime解析
        default: 当无法格式化时返回的默认值

    Returns:
        格式化后的时间字符串
    """
    if not dt:
        return default

    try:
        if isinstance(dt, str):
            if input_format:
                dt = datetime.strptime(dt.strip(), input_format).date()
            else:
                dt = date.fromisoformat(dt.strip())
        if isinstance(dt, date):
            return dt.strftime(output_format)
    except (ValueError, TypeError):
        pass

    return default


def get_timestamp() -> int:
    """获取当前时间戳

    返回当前时间的Unix时间戳（从1970年1月1日UTC零点开始的秒数）。
    时间戳为整数，精确到秒。

    Returns:
        int: 当前时间的Unix时间戳

    Examples:
        >>> get_timestamp()
        1709251200  # 2024-03-01 00:00:00 UTC
    """
    return int(datetime.now().timestamp())
