"""通用工具函数模块

包含:
- 数字格式化
- 样式常量
- 工具函数
"""

from datetime import datetime
from typing import Any, Dict

# ============= 样式常量 =============
CARD_STYLES = {
    "height": "100%",
    "borderRadius": "12px",
    "boxShadow": "0 2px 8px rgba(0, 0, 0, 0.08)",
    "transition": "all 0.3s ease",
    "background": "linear-gradient(to bottom, #ffffff, #fafafa)",
}

CARD_HOVER_STYLES = {
    "boxShadow": "0 4px 16px rgba(24, 144, 255, 0.12)",
    "transform": "translateY(-2px)",
}

CARD_HEAD_STYLES = {
    "borderBottom": "none",
    "padding": "16px 24px 0 24px",
    "fontSize": "16px",
    "fontWeight": "500",
    "color": "#262626",
    "textAlign": "center",
}

ICON_STYLES = {
    "fontSize": "24px",
    "marginRight": "8px",
}


# ============= 工具函数 =============
def format_money(amount: float) -> str:
    """格式化金额显示

    Args:
        amount: 金额数值

    Returns:
        格式化后的金额字符串,如: ¥ 1,234.56
    """
    return f"¥ {amount:,.2f}"


def format_percent(value: float) -> str:
    """格式化百分比显示

    Args:
        value: 百分比数值

    Returns:
        格式化后的百分比字符串,如: 12.34%
    """
    return f"{value:.2f}%"


def format_datetime(dt: datetime) -> str:
    """格式化日期时间显示

    Args:
        dt: 日期时间对象

    Returns:
        格式化后的日期时间字符串
    """
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def get_value_color(value: float) -> str:
    """根据数值获取显示颜色

    Args:
        value: 要判断的数值

    Returns:
        颜色代码
    """
    if value > 0:
        return "#52c41a"  # 绿色
    elif value < 0:
        return "#f5222d"  # 红色
    else:
        return "#8c8c8c"  # 灰色


def safe_get(data: Dict[str, Any], key: str, default: Any = 0) -> Any:
    """安全地获取字典值

    Args:
        data: 源字典
        key: 键名
        default: 默认值

    Returns:
        获取到的值或默认值
    """
    try:
        return data.get(key, default)
    except:
        return default
