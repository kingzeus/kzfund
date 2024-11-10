import time
from datetime import datetime
from typing import Dict, Any
import logging
from .base import BaseTask
from data_source.proxy import DataSourceProxy
from models.fund import Fund

logger = logging.getLogger(__name__)


class FundInfoTask(BaseTask):
    """基金信息更新任务"""

    @classmethod
    def get_type(cls) -> str:
        return "fund_info"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        return {
            "name": "基金信息更新",
            "description": "更新基金基本信息",
            "timeout": 300,
            "priority": 2,
            "params": [
                {
                    "name": "基金代码",
                    "key": "fund_code",
                    "type": "fund-select",  # 使用基金选择器组件
                    "required": True,
                    "description": "要更新的基金代码",
                }
            ],
        }

    @classmethod
    def get_description(cls) -> str:
        return "更新基金基本信息"

    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info(f"[{datetime.now()}] 开始更新基金信息 {self.task_id}")

        # 获取参数
        fund_code = kwargs.get("fund_code")
        if not fund_code:
            raise ValueError("fund_code is required")

        try:
            # 初始化数据源
            data_source = DataSourceProxy()

            # 更新进度
            self.update_progress(20)
            logger.info(f"正在获取基金 {fund_code} 的信息...")

            # 获取基金信息
            fund_info = data_source.get_fund_info(fund_code)

            # 检查必要字段是否存在，设置默认值
            fund_data = {
                "name": fund_info.get("name", "未知名称"),
                "type": fund_info.get("type", "未知类型"),  # 添加默认值
                "company": fund_info.get("company", "未知公司"),
                "description": fund_info.get("description", ""),
            }

            self.update_progress(50)
            logger.info("正在更新数据库...")

            # 更新或创建基金记录
            fund, created = Fund.get_or_create(code=fund_code, defaults=fund_data)

            if not created:
                # 更新现有记录
                for key, value in fund_data.items():
                    setattr(fund, key, value)
                fund.save()

            self.update_progress(80)
            logger.info("正在获取最新净值...")

            # # 获取最新净值
            # nav_history = data_source.get_fund_nav_history(
            #     fund_code,
            #     start_date=datetime.now().replace(
            #         hour=0, minute=0, second=0, microsecond=0
            #     ),
            # )

            # if nav_history:
            #     latest_nav = nav_history[0]
            #     fund.nav = latest_nav.get("nav")
            #     nav_date = latest_nav.get("date")
            #     if nav_date:
            #         fund.nav_date = datetime.strptime(nav_date, "%Y-%m-%d")
            #     fund.save()

            self.update_progress(100)
            logger.info(f"基金 {fund_code} 信息更新完成")

            return {
                "message": "Fund info update completed",
                "task_id": self.task_id,
                "fund_code": fund_code,
                "fund_name": fund_data["name"],
                "created": created,
                "nav": str(fund.nav) if fund.nav else None,
                "nav_date": fund.nav_date.strftime("%Y-%m-%d")
                if fund.nav_date
                else None,
            }

        except Exception as e:
            logger.error(
                f"更新基金信息失败: {str(e)}", exc_info=True
            )  # 添加完整的错误堆栈
            raise
