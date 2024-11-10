from typing import Dict, Any
from datetime import datetime
from peewee import *
from playhouse.shortcuts import model_to_dict
from .base import BaseModel


class TaskHistory(BaseModel):
    task_id = CharField(max_length=36, primary_key=True)
    name = CharField(max_length=100)
    priority = IntegerField(default=0)  # 优先级：数字越大优先级越高
    status = CharField(max_length=20)
    progress = IntegerField(default=0)
    result = TextField(null=True)
    error = TextField(null=True)
    start_time = DateTimeField(null=True)
    end_time = DateTimeField(null=True)
    timeout = IntegerField(default=3600)  # 超时时间（秒）
    created_at = DateTimeField(default=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return model_to_dict(self)
