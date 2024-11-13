from typing import Any
from flask_restx import fields, Model


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
