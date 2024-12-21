import logging
from datetime import datetime
from random import Random
from typing import Any, Dict

from data_source.proxy import DataSourceProxy
from kz_dash.models.database import get_record
from models.fund import ModelFund
from kz_dash.scheduler.task_factory import TaskFactory
from kz_dash.utility.datetime_helper import get_date_str_after_days, get_days_between_dates

from task.task_config import PARAM_FUND_CODE, PARAM_SUB_TASK_DELAY
from kz_dash.scheduler.base_task import BaseTask

logger = logging.getLogger(__name__)

# 创建Random实例
random = Random()


class SyncFundNavTask(BaseTask):
    """基金净值更新任务"""

    @classmethod
    def get_type(cls) -> str:
        return "sync_fund_nav"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        return {
            "name": "【同步】基金历史净值",
            "description": "同步单个基金历史净值",
            "timeout": 300,
            "params": [PARAM_FUND_CODE, PARAM_SUB_TASK_DELAY],
        }

    @classmethod
    def get_description(cls) -> str:
        return "同步单个基金历史净值"

    def execute(self, **kwargs) -> Dict[str, Any]:
        from scheduler.job_manager import JobManager

        logger.info("[%s] 开始同步基金净值 %s", datetime.now(), self.task_id)

        # 获取参数
        fund_code = kwargs.get("fund_code")
        if not fund_code:
            raise ValueError("fund_code 不能为空")

        sub_task_delay = kwargs.get("sub_task_delay", 2)

        try:
            # 初始化数据源
            data_source = DataSourceProxy()

            # 1.获取基金信息,确定基金起始日期
            fund_info = get_record(ModelFund, {"code": fund_code})
            if fund_info:
                start_date = fund_info.establishment_date.strftime("%Y-%m-%d")
            else:
                result = TaskFactory().execute_task(
                    "fund_detail", self.task_id, fund_code=fund_code
                )
                start_date = result.get("establishment_date")
            self.update_progress(5)
            # 获取基金历史净值数据大小
            nav_history_size_response = data_source.get_fund_nav_history_size()
            if nav_history_size_response["code"] != 200:
                raise ValueError(nav_history_size_response["message"])

            # 2.计算日期区间
            today = datetime.now().strftime("%Y-%m-%d")
            days_per_task = nav_history_size_response["data"]

            # 3.批量添加任务
            current_date = start_date
            delay = 0
            tasks = []

            while get_days_between_dates(current_date, today) >= 0:
                # 计算结束日期
                end_date = get_date_str_after_days(current_date, days_per_task)
                if get_days_between_dates(today, end_date) > 0:
                    end_date = today

                logger.info("添加任务: %s [%s-%s]", fund_code, current_date, end_date)

                # 添加任务
                sub_task_id = JobManager().add_task(
                    "fund_nav",
                    parent_task_id=self.task_id,
                    fund_code=fund_code,
                    start_date=current_date,
                    end_date=end_date,
                    delay=delay,
                )
                tasks.append(sub_task_id)

                # 更新下一个任务的起始日期和延迟时间
                current_date = get_date_str_after_days(end_date, 1)
                delay += random.randint(0, sub_task_delay)

            self.update_progress(10)
            logger.info("成功添加 %d 个任务", len(tasks))
            return {"tasks": tasks}

        except Exception as e:
            logger.error("同步基金净值失败: %s", str(e), exc_info=True)  # 添加完整的错误堆栈
            raise