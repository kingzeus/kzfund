import json
import unittest
from datetime import date, datetime

from data_source.implementations.eastmoney import EastMoneyDataSource


class TestDataSource(unittest.TestCase):
    """测试数据源功能"""

    def setUp(self):
        """测试前的准备工作"""
        self.data_source = EastMoneyDataSource()
        self.maxDiff = None  # 显示完整的差异信息

    def assertFieldNotEmpty(self, data: dict, field: str, actual_value=None):
        """
        断言字段不为空，并提供详细的错误信息

        Args:
            data: 要检查的数据字典
            field: 要检查的字段名
            actual_value: 字段的实际值（如果已经获取）
        """
        value = actual_value if actual_value is not None else data.get(field)

        # 准备详细的错误信息
        error_msg = [
            f"\n字段验证失败: {field}",
            "期望: 非空值",
            f"实际: {value!r}",
            "\n完整数据:",
            json.dumps(data, indent=2, ensure_ascii=False, default=str),
        ]

        self.assertIn(field, data, f"缺少必需字段: {field}\n{error_msg}")
        self.assertIsNotNone(value, "\n".join(error_msg))

    def assertIsValidDate(self, value, field_name: str):
        """
        断言值是有效的date对象

        Args:
            value: 要检查的值
            field_name: 字段名称
        """
        error_msg = [
            f"\n日期字段验证失败: {field_name}",
            "期望: date对象",
            f"实际: {type(value)} = {value!r}",
        ]

        self.assertTrue(isinstance(value, (date, str)), "\n".join(error_msg))

    def assertIsValidPercentage(self, value, field_name: str):
        """
        断言值是有效的百分比

        Args:
            value: 要检查的值
            field_name: 字段名称
        """
        try:
            # 移除百分号并转换为浮点数
            float_value = float(str(value).rstrip("%"))
            error_msg = [
                f"\n百分比字段验证失败: {field_name}",
                "期望: 有效的百分比值",
                f"实际: {value!r}",
                f"转换后: {float_value}",
            ]

            self.assertIsInstance(float_value, float, "\n".join(error_msg))
        except (ValueError, TypeError) as e:
            self.fail(f"\n百分比转换失败: {field_name}\n" f"值: {value!r}\n" f"错误: {str(e)}")

    def test_get_fund_detail(self):
        """测试获取基金详情功能"""
        fund_code = "012348"
        fund_detail = self.data_source.get_fund_detail(fund_code)

        # 首先打印完整的返回数据，方便调试
        print(f"\n获取到的基金详情 ({fund_code}):")
        print(json.dumps(fund_detail, indent=2, ensure_ascii=False, default=str))

        # 验证结果不为空
        self.assertIsNotNone(fund_detail, "获取基金详情失败，返回为空")

        # 验证基本字段
        required_fields = [
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
            "data_source",
            "data_source_version",
        ]

        # 验证所有必需字段存在且不为空
        for field in required_fields:
            self.assertFieldNotEmpty(fund_detail, field)

        # 验证日期字段
        date_fields = ["issue_date", "establishment_date"]
        for field in date_fields:
            self.assertIsValidDate(fund_detail[field], field)

        # 验证百分比字段
        percentage_fields = ["management_fee", "custodian_fee", "sales_service_fee"]
        for field in percentage_fields:
            self.assertIsValidPercentage(fund_detail[field], field)

        # 验证特定字段的值
        self.assertEqual(
            fund_detail["code"],
            fund_code,
            f"基金代码不匹配\n期望: {fund_code}\n实际: {fund_detail['code']}",
        )

        # 验证数据源信息
        self.assertEqual(fund_detail["data_source"], "eastmoney", "数据源标识不正确")
        self.assertIsNotNone(fund_detail["data_source_version"], "数据源版本不能为空")

    def test_get_fund_nav_history(self):
        """测试获取基金净值历史功能"""
        fund_code = "161725"
        start_date = datetime(2021, 8, 31)
        end_date = datetime(2021, 9, 8)
        nav_history = self.data_source.get_fund_nav_history(fund_code, start_date, end_date)

        # 打印完整的返回数据，方便调试
        print("\n获取到的基金净值历史:")
        print(json.dumps(nav_history[:3], indent=2, ensure_ascii=False, default=str))

        # 验证结果不为空
        self.assertIsNotNone(nav_history, "获取基金净值历史失败，返回为空")
        self.assertGreater(len(nav_history), 0, "基金净值历史记录为空")

        # 验证第一条记录的字段
        first_record = nav_history[0]
        required_fields = [
            "nav_date",
            "nav",
            "acc_nav",
            "daily_return",
            "subscription_status",
            "redemption_status",
        ]

        # 验证所有必需字段存在且不为空
        for field in required_fields:
            self.assertFieldNotEmpty(first_record, field)

        # 验证日期字段
        self.assertIsValidDate(first_record["nav_date"], "date")

        # 验证数值字段
        self.assertIsInstance(float(first_record["nav"]), float, "单位净值必须是有效的数值")
        self.assertIsInstance(float(first_record["acc_nav"]), float, "累计净值必须是有效的数值")

        # 验证日增长率为百分比格式
        self.assertIsValidPercentage(first_record["daily_return"], "daily_return")

        # 验证记录按日期降序排序
        dates = [record["nav_date"] for record in nav_history[:2]]
        self.assertGreater(dates[0], dates[1], "净值历史记录未按日期降序排序")

    def test_get_fund_nav_list(self):
        """测试获取基金净值列表功能"""
        # 使用默认参数获取第一页数据
        nav_list = self.data_source.get_fund_nav_list(page_size=2)

        # 打印完整的返回数据，方便调试
        print("\n获取到的基金净值列表:")
        print(nav_list)

        # 验证结果不为空
        self.assertIsNotNone(nav_list, "获取基金净值列表失败，返回为空")

        # 验证第一条记录的字段
        nav_list["items"][0]

    def tearDown(self):
        """测试后的清理工作"""


if __name__ == "__main__":
    unittest.main(verbosity=2)
