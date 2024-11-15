import unittest
import uuid
import json
from data_source.data_source_factory import DataSourceFactory
from data_source.implementations.eastmoney import EastMoneyDataSource
from scheduler.tasks.fund_detail import FundDetailTask


class TestFundDetailTasks(unittest.TestCase):
    """测试基金详情任务功能"""

    def setUp(self):
        """测试前的准备工作"""
        self.maxDiff = None  # 显示完整的差异信息
        # 注册数据源
        DataSourceFactory.register(EastMoneyDataSource)

        self.task = FundDetailTask(str(uuid.uuid4()))

    def assertTaskResult(self, result: dict, expected_fields: list):
        """
        断言任务执行结果

        Args:
            result: 任务执行结果
            expected_fields: 期望包含的字段列表
        """
        # 打印完整的任务结果，方便调试
        print("\n任务执行结果:")
        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))

        # 验证结果不为空
        self.assertIsNotNone(result, "任务执行失败，返回为空")

        # 验证必要字段
        for field in expected_fields:
            self.assertIn(
                field,
                result,
                f"\n缺少必需字段: {field}\n完整数据:\n{json.dumps(result, indent=2, ensure_ascii=False, default=str)}",
            )

    def test_task_execution(self):
        """测试任务执行"""
        # 准备测试数据
        fund_code = "012348"

        # 执行任务
        results = self.task.execute(fund_code=fund_code)

        # 验证结果
        self.assertIsNotNone(results, "任务执行失败，返回为空")
        # 验证返回格式符合统一响应格式
        self.assertIsInstance(results, dict, "返回结果应为字典类型")
        # 验证基金详情字段
        expected_fields = [
            "code",
            "name",
            "full_name",
            "type",
            "issue_date",
            "establishment_date",
            "establishment_size",
            "company",
            "custodian",
            "fund_manager",
            "management_fee",
            "custodian_fee",
            "sales_service_fee",
            "tracking",
            "performance_benchmark",
            "investment_scope",
            "investment_target",
            "investment_philosophy",
            "investment_strategy",
            "dividend_policy",
            "risk_return_characteristics",
            "data_source",
            "data_source_version",
        ]
        self.assertTaskResult(results, expected_fields)

        # 验证字段值的有效性
        self.assertEqual(results["code"], fund_code, "基金代码不匹配")
        self.assertIsNotNone(results["name"], "基金名称不能为空")
        self.assertIsNotNone(results["full_name"], "基金全称不能为空")
        self.assertIsNotNone(results["type"], "基金类型不能为空")
        self.assertIsNotNone(results["company"], "基金公司不能为空")

        # 验证数值字段
        self.assertIsInstance(
            results["establishment_size"], (int, float), "成立规模应为数值类型"
        )
        self.assertIsInstance(
            results["management_fee"], (int, float), "管理费率应为数值类型"
        )
        self.assertIsInstance(
            results["custodian_fee"], (int, float), "托管费率应为数值类型"
        )
        self.assertIsInstance(
            results["sales_service_fee"], (int, float), "销售服务费率应为数值类型"
        )

    def tearDown(self):
        """测试后的清理工作"""


if __name__ == "__main__":
    unittest.main(verbosity=2)
