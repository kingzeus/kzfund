from typing import Dict, Any, Optional, Type, List
from flask_restx import fields, Model

def response(
    data: Optional[Dict[str, Any]] = None,
    message: str = "success",
    code: int = 200,
) -> Dict[str, Any]:
    """统一的API响应格式"""
    return {
        "code": code,
        "message": message,
        "data": data or [],
    }



def create_response_model(api: Any, name: str, data_model: Model) -> Model:
    """创建统一的响应模型"""
    return api.model(
        f"{name}Response",
        {
            "code": fields.Integer(description="响应代码"),
            "message": fields.String(description="响应消息"),
            "data": fields.Nested(data_model, description="响应数据"),
        },
    )


def create_list_response_model(api: Any, name: str, data_model: Model) -> Model:
    """创建统一的列表响应模型"""
    return api.model(
        f"{name}ListResponse",
        {
            "code": fields.Integer(description="响应代码"),
            "message": fields.String(description="响应消息"),
            "data": fields.List(fields.Nested(data_model), description="响应数据列表"),
        },
    )
