import json
import unittest
from datetime import date

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

    def tearDown(self):
        """测试后的清理工作"""


if __name__ == "__main__":
    unittest.main(verbosity=2)
