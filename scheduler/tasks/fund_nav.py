import logging
from datetime import datetime
from typing import Any, Dict

from data_source.proxy import DataSourceProxy
from models.database import update_record
from models.fund import ModelFundNav
from utils.datetime_helper import get_date_str_after_days, get_days_between_dates

from .base import BaseTask

logger = logging.getLogger(__name__)


class FundNavTask(BaseTask):
    """基金净值更新任务"""

    @classmethod
    def get_type(cls) -> str:
        return "fund_nav"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        return {
            "name": "基金净值更新",
            "description": "更新基金净值",
            "timeout": 300,
            "params": [
                {
                    "name": "基金代码",
                    "key": "fund_code",
                    "type": "fund-code-aio",  # 使用基金选择器组件
                    "required": True,
                    "description": "要更新的基金代码",
                },
                {
                    "name": "开始日期",
                    "key": "start_date",
                    "type": "date",
                    "required": True,
                    "description": "开始日期",
                },
                {
                    "name": "结束日期",
                    "key": "end_date",
                    "type": "date",
                    "description": "结束日期",
                },
            ],
        }

    @classmethod
    def get_description(cls) -> str:
        return "更新基金净值"

    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info("[%s] 开始更新基金净值 %s", datetime.now(), self.task_id)

        # 获取参数
        fund_code = kwargs.get("fund_code")
        if not fund_code:
            raise ValueError("fund_code 不能为空")
        start_date = kwargs.get("start_date")
        if not start_date:
            raise ValueError("start_date 不能为空")
        end_date = kwargs.get("end_date")

        try:
            # 初始化数据源
            data_source = DataSourceProxy()

            # 获取基金历史净值数据大小
            nav_history_size_response = data_source.get_fund_nav_history_size()
            if nav_history_size_response["code"] != 200:
                raise ValueError(nav_history_size_response["message"])
            self.update_progress(30)

            if not end_date:
                # 默认结束日期是 开始日期
                end_date = get_date_str_after_days(start_date, nav_history_size_response["data"])
            else:
                size = get_days_between_dates(start_date, end_date)
                if size < 0:
                    raise ValueError("结束日期不能早于开始日期")
                if size > nav_history_size_response["data"]:
                    raise ValueError("查询日期数量过大")

            # 更新进度
            self.update_progress(50)
            logger.info("正在获取基金 %s [%s-%s] 的净值...", fund_code, start_date, end_date)

            # 获取基金信息
            nav_history_response = data_source.get_fund_nav_history(fund_code, start_date, end_date)

            self.update_progress(70)
            if nav_history_response["code"] != 200:
                raise ValueError(nav_history_response["message"])

            logger.info("正在更新数据库...")
            # 批量保存净值到数据库
            nav_data = nav_history_response["data"]
            for nav_item in nav_data:
                update_record(
                    ModelFundNav,
                    {"fund_code": fund_code, "nav_date": nav_item["nav_date"]},
                    nav_item,
                )

            self.update_progress(100)
            logger.info("基金 %s 信息更新完成", fund_code)

            return nav_history_response["data"]

        except Exception as e:
            logger.error("更新基金信息失败: %s", str(e), exc_info=True)  # 添加完整的错误堆栈
            raise
