#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from flask_restx import Resource, Namespace, fields
from flask import request
from scheduler.job_manager import JobManager
import uuid

from utils import response
from .common import create_response_model, create_list_response_model
from scheduler.tasks import TaskFactory

logger = logging.getLogger(__name__)

api = Namespace("tasks", description="任务管理")


# 定义基础数据模型
task_base = api.model(
    "TaskBase",
    {
        "task_id": fields.String(required=True, description="任务ID"),
        "name": fields.String(required=True, description="任务名称"),
        "priority": fields.Integer(required=True, description="优先级"),
        "status": fields.String(required=True, description="任务状态"),
        "progress": fields.Integer(required=True, description="进度"),
        "result": fields.String(description="执行结果"),
        "error": fields.String(description="错误信息"),
        "start_time": fields.DateTime(description="开始时间"),
        "end_time": fields.DateTime(description="结束时间"),
        "timeout": fields.Integer(required=True, description="超时时间(秒)"),
        "created_at": fields.DateTime(required=True, description="创建时间"),
    },
)

# 使用通用函数创建响应模型
task_response = create_response_model(api, "Task", task_base)
task_list_response = create_list_response_model(api, "Task", task_base)

# 定义任务创建输入模型
task_input = api.model(
    "TaskInput",
    {
        "type": fields.String(
            required=True,
            description="任务类型",
            enum=list(TaskFactory().get_task_types().keys()),
        ),
        "priority": fields.Integer(description="优先级"),
        "timeout": fields.Integer(description="超时时间(秒)"),
        "params": fields.Raw(description="任务参数"),
    },
)


@api.route("/tasks")
class TaskList(Resource):
    @api.doc("获取任务历史")
    @api.param("limit", "返回记录数量限制", type=int)
    @api.marshal_with(task_list_response)
    def get(self):
        """获取任务历史列表"""
        limit = request.args.get("limit", 100, type=int)
        return response(data=JobManager().get_task_history(limit))

    @api.doc("创建新任务")
    @api.expect(task_input)
    @api.marshal_with(task_response)
    def post(self):
        """创建新任务"""
        data = api.payload
        task_type = data["type"]

        if task_type not in TaskFactory().get_task_types():
            return response(message="未知的任务类型", code=400)

        # 创建任务
        task_id = JobManager().add_task(
            task_type=task_type,
            priority=data.get("priority"),
            timeout=data.get("timeout"),
            **(data.get("params", {})),
        )

        return response(data={"task_id": task_id}, message="任务创建成功")


@api.route("/tasks/<string:task_id>")
@api.param("task_id", "任务ID")
class Task(Resource):
    @api.doc("获取任务状态")
    @api.marshal_with(task_response)
    def get(self, task_id):
        """获取指定任务的状态"""
        status = JobManager.get_task_status(task_id)
        if status.get("status") == "not_found":
            return response(message="任务不存在", code=404)
        return response(data=status)

    @api.doc("暂停任务")
    @api.marshal_with(task_response)
    def put(self, task_id):
        """暂停任务"""
        if JobManager.pause_task(task_id):
            return response(message="任务已暂停")
        return response(message="任务不存在或无法暂停", code=404)

    @api.doc("恢复任务")
    @api.marshal_with(task_response)
    def post(self, task_id):
        """恢复任务"""
        if JobManager.resume_task(task_id):
            return response(message="任务已恢复")
        return response(message="任务不存在或无法恢复", code=404)