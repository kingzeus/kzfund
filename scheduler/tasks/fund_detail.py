import time
from datetime import datetime
from typing import Dict, Any
import logging
from .base import BaseTask
from data_source.proxy import DataSourceProxy
from models.fund import Fund

logger = logging.getLogger(__name__)


class FundDetailTask(BaseTask):
    """基金详情更新任务"""

    @classmethod
    def get_type(cls) -> str:
        return "fund_detail"

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        return {
            "name": "基金详情更新",
            "description": "更新基金详情信息",
            "timeout": 30,
            "priority": 2,
            "params": [
                {
                    "name": "基金代码",
                    "key": "fund_code",
                    "type": "fund-code-aio",  # 使用基金选择器组件
                    "required": True,
                    "description": "要更新的基金代码",
                }
            ],
        }

    @classmethod
    def get_description(cls) -> str:
        return "更新基金详情信息"

    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info(f"[{datetime.now()}] 开始更新基金详情 {self.task_id}")

        # 获取参数
        fund_code = kwargs.get("fund_code")
        if not fund_code:
            raise ValueError("fund_code is required")

        try:
            # 初始化数据源
            data_source = DataSourceProxy()
            # 更新进度
            self.update_progress(20)
            logger.info(f"正在获取基金 {fund_code} 的详情...")
            # 获取基金信息
            fund_info_response = data_source.get_fund_detail(fund_code)
            self.update_progress(70)
            if fund_info_response["code"] != 200:
                raise ValueError(fund_info_response["message"])
            fund_info = fund_info_response["data"]

            # 检查必要字段是否存在，设置默认值
            fund_data = {
                "code": fund_info.get("code"),
                "name": fund_info.get("name", "未知名称"),
                "full_name": fund_info.get("full_name", "未知全称"),
                "type": fund_info.get("type", "未知类型"),
                "issue_date": fund_info.get("issue_date"),
                "establishment_date": fund_info.get("establishment_date"),
                "establishment_size": fund_info.get("establishment_size", 0),
                "company": fund_info.get("company", "未知公司"),
                "custodian": fund_info.get("custodian", "未知托管人"),
                "fund_manager": fund_info.get("fund_manager", "未知基金经理"),
                "management_fee": fund_info.get("management_fee", 0),
                "custodian_fee": fund_info.get("custodian_fee", 0),
                "sales_service_fee": fund_info.get("sales_service_fee", 0),
                "tracking": fund_info.get("tracking", ""),
                "performance_benchmark": fund_info.get("performance_benchmark", ""),
                "investment_scope": fund_info.get("investment_scope", ""),
                "investment_target": fund_info.get("investment_target", ""),
                "investment_philosophy": fund_info.get("investment_philosophy", ""),
                "investment_strategy": fund_info.get("investment_strategy", ""),
                "dividend_policy": fund_info.get("dividend_policy", ""),
                "risk_return_characteristics": fund_info.get(
                    "risk_return_characteristics", ""
                ),
                "data_source": fund_info.get("data_source"),
                "data_source_version": fund_info.get("data_source_version"),
            }

            self.update_progress(80)
            logger.info("正在更新数据库...")

            # 更新或创建基金记录
            fund, created = Fund.get_or_create(code=fund_code, defaults=fund_data)

            if not created:
                # 更新现有记录
                for key, value in fund_data.items():
                    setattr(fund, key, value)
                fund.save()

            self.update_progress(100)
            logger.info(f"基金 {fund_code} 信息更新完成")

            return fund_data

        except Exception as e:
            logger.error(
                f"更新基金信息失败: {str(e)}", exc_info=True
            )  # 添加完整的错误堆栈
            raise