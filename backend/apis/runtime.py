#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime
from flask_restx import Resource, Namespace, fields
from config import VERSION
from utils import response
from .common import create_response_model

logger = logging.getLogger(__name__)

api = Namespace("runtime", description="运行时状态")

# 记录应用启动时间
DEPLOY_TIME = datetime.now()

# 定义基础数据模型
runtime_base = api.model(
    "RuntimeBase",
    {
        "deploy_time": fields.String(description="部署时间"),
        "uptime": fields.String(description="运行时间"),
        "version": fields.String(description="版本号"),
    },
)

# 使用通用函数创建响应模型
runtime_response = create_response_model(api, "Runtime", runtime_base)

@api.route("/status")
class RuntimeStatus(Resource):
    @api.doc("获取运行时状态")
    @api.marshal_with(runtime_response)
    def get(self):
        """获取系统运行状态"""
        now = datetime.now()
        uptime = now - DEPLOY_TIME

        # 计算运行时间
        total_seconds = uptime.total_seconds()
        days = int(total_seconds // (24 * 3600))
        hours = int((total_seconds % (24 * 3600)) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        return response(
            data={
                "deploy_time": DEPLOY_TIME.strftime("%Y-%m-%d %H:%M:%S"),
                "uptime": f"{days}天{hours}时{minutes}分{seconds}秒",
                "version": VERSION,
            },
            message="获取运行时状态成功",
        )
