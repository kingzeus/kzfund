#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
from datetime import datetime

from flask_restx import Resource
from flask_restx.namespace import Namespace
from .common import response
import time


logger = logging.getLogger(__name__)

api = Namespace("run", description="运行时间")

deploy_time = datetime.now()


@api.route("/runtime")
class RuntimeResource(Resource):
    def get(self):
        """运行时间"""
        run_time = (datetime.now() - deploy_time).total_seconds()
        year = run_time // (365 * 24 * 3600)
        run_time -= year * 365 * 24 * 3600
        day = run_time // (24 * 3600)
        run_time -= day * 24 * 3600
        hour = run_time // 3600
        run_time %= 3600
        minute = run_time // 60
        seconds = run_time % 60

        logger.info("test")
        return response(
            data={
                "上次部署时间": deploy_time.strftime("%y-%m-%d %H:%M:%S"),
                "运行时间": "{}年{}天{}时{}分{}秒".format(
                    int(year), int(day), int(hour), int(minute), int(seconds)
                ),
            }
        )
