from typing import Dict, Any, Optional
from flask import jsonify


def response(
    data: Optional[Dict[str, Any]] = None,
    message: str = "success",
    code: int = 200,
) -> Dict[str, Any]:
    """统一的API响应格式"""
    return {
        "code": code,
        "message": message,
        "data": data or {},
    }
