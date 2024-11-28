import logging
from datetime import datetime
from random import Random
from typing import Any, Dict

from data_source.proxy import DataSourceProxy
from models.database import get_record, get_record_count, update_record
from models.fund import ModelFund, ModelFundNav
from scheduler.tasks.task_factory import TaskFactory
from utils.datetime_helper import get_date_str_after_days, get_days_between_dates

from .base import PARAM_FUND_TYPE, PARAM_PAGE, PARAM_PAGE_SIZE, PARAM_SUB_TASK_DELAY, BaseTask

logger = logging.getLogger(__name__)

# 创建Random实例
random = Random()

class SyncFundListPageTask(BaseTask):
    """基金列表更新任务"""

    @classmethod
    def get_type(cls) -> str:
        return "sync_fund_page"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        return {
            "name": "【同步】基金最新净值列表页",
            "description": "基金最新净值列表页",
            "timeout": 300,
            "params": [
                PARAM_FUND_TYPE,
                PARAM_PAGE,
                PARAM_PAGE_SIZE,
                PARAM_SUB_TASK_DELAY,
                {
                    "name": "是否获取历史净值",
                    "key": "history_nav",
                    "type": "boolean",
                    "required": False,
                    "default": True,
                    "description": "没有历史净值，是否同步历史净值",
                },
            ],
        }

    @classmethod
    def get_description(cls) -> str:
        return "基金最新净值列表页"

    def execute(self, **kwargs) -> Dict[str, Any]:
        from scheduler.job_manager import JobManager

        logger.info("[%s] 开始同步基金净值列表页 %s", datetime.now(), self.task_id)

        # 获取参数
        type = kwargs.get("fund_type")
        if not type:
            raise ValueError("fund_type 不能为空")
        page = kwargs.get("page")
        if not page:
            raise ValueError("page 不能为空")
        page_size = kwargs.get("page_size")
        if not page_size:
            raise ValueError("page_size 不能为空")
        history_nav = kwargs.get("history_nav")
        sub_task_delay = kwargs.get("sub_task_delay", 2)
        try:
            # 初始化数据源
            data_source = DataSourceProxy()

            delay = 0
            index = 0
            # 1. 获取列表页数据
            fund_list_response = data_source.get_fund_nav_list(
                type=type, page=page, page_size=page_size
            )
            if fund_list_response["code"] != 200:
                raise ValueError(fund_list_response["message"])
            self.update_progress(10)

            # 2. 遍历基金列表
            for fund in fund_list_response["data"]["items"]:
                # 3. 获取基金信息
                fund_info = get_record(ModelFund, {"code": fund["fund_code"]})
                if not fund_info:
                    # 3.1 同步基金信息
                    JobManager().add_task(
                        "fund_detail",
                        parent_task_id=self.task_id,
                        fund_code=fund["fund_code"],
                        delay=delay,
                    )
                    delay += random.randint(0, sub_task_delay)

                # 3.2 如果没有历史数据，则同步历史数据
                history_count = get_record_count(ModelFundNav, {"fund_code": fund["fund_code"]})
                if history_nav and history_count == 0:
                    # 3.3 添加同步历史数据任务
                    JobManager().add_task(
                        "sync_fund_nav",
                        parent_task_id=self.task_id,
                        fund_code=fund["fund_code"],
                        delay=delay,
                    )
                    delay += random.randint(0, sub_task_delay)
                else:
                    # 3.4 更新基金净值
                    update_record(
                        ModelFundNav,
                        {"fund_code": fund["fund_code"], "nav_date": fund["nav_date"]},
                        fund,
                    )
                self.update_progress(10 + 90 * (index / len(fund_list_response["data"]["items"])))
                index += 1

            self.update_progress(100)
            return fund_list_response

        except Exception as e:
            logger.error("同步基金净值失败: %s", str(e), exc_info=True)
            raise
