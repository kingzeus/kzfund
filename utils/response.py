from typing import Dict, Any, Optional


def response(
    data: Optional[Any] = None,
    message: str = "success",
    is_array: bool = True,
    code: int = 200,
) -> Dict[str, Any]:
    """统一的响应格式

    Args:
        data: 响应数据
        message: 响应消息
        is_array: 数据是否为数组类型
        code: 响应代码

    Returns:
        统一格式的响应字典
    """
    return {
        "code": code,
        "message": message,
        "data": data or ([] if is_array else None),
    }
