import logging
from datetime import date, datetime, timedelta
from typing import Optional, Union

logger = logging.getLogger(__name__)


def format_datetime(
    dt: Union[str, datetime, None],
    output_format: str = "%Y-%m-%d %H:%M:%S",
    default: str = "未知时间",
) -> str:
    """
    统一的日期时间格式化函数

    Args:
        dt: 要格式化的日期时间，可以是datetime对象或ISO格式的字符串
        output_format: 输出格式，默认为 "%Y-%m-%d %H:%M:%S"
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
            return dt.strftime(output_format)
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


def get_date_str_after_days(start_date: Union[str, date], days: int) -> str:
    """获取开始日期后几天的日期字符串"""
    return format_date(get_date_after_days(start_date, days))


def get_days_between_dates(start_date: Union[str, date], end_date: Union[str, date]) -> int:
    """计算两个日期之间的天数差值

    Args:
        start_date: 开始日期,可以是date对象或ISO格式字符串
        end_date: 结束日期,可以是date对象或ISO格式字符串

    Returns:
        int: 两个日期之间的天数差值(end_date - start_date)

    Examples:
        >>> get_days_between_dates('2024-03-01', '2024-03-02')
        1
        >>> get_days_between_dates(date(2024, 3, 1), date(2024, 2, 29))
        -1
    """
    try:
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date.strip())
        if isinstance(end_date, str):
            end_date = date.fromisoformat(end_date.strip())

        if not isinstance(start_date, date) or not isinstance(end_date, date):
            logger.error("无效的日期格式: start_date=%s, end_date=%s", start_date, end_date)
            raise ValueError("无效的日期格式")

        return (end_date - start_date).days

    except (ValueError, TypeError) as e:
        logger.error("计算日期差值失败: %s", str(e))
        raise


def get_date_after_days(start_date: Union[str, date], days: int) -> date:
    """获取开始日期后几天的日期

    Args:
        start_date: 开始日期,可以是date对象或ISO格式字符串
        days: 天数,正数表示往后,负数表示往前

    Returns:
        date: 计算后的日期

    Examples:
        >>> get_date_after_days('2024-03-01', 1)
        datetime.date(2024, 3, 2)
        >>> get_date_after_days(date(2024, 3, 1), -1)
        datetime.date(2024, 2, 29)
    """
    try:
        if isinstance(start_date, str):
            start_date = date.fromisoformat(start_date.strip())

        if not isinstance(start_date, date):
            logger.error("无效的日期格式: %s", start_date)
            raise ValueError("无效的日期格式")

        return start_date + timedelta(days=days)

    except (ValueError, TypeError) as e:
        logger.error("计算日期失败: %s", str(e))
        raise
