import unittest
from datetime import datetime, date
from utils.datetime import format_datetime, format_date, get_timestamp


class TestDatetimeFunctions(unittest.TestCase):
    def test_format_datetime(self):
        # 测试datetime对象
        dt = datetime(2021, 7, 6, 12, 30)
        self.assertEqual(format_datetime(dt), "2021-07-06 12:30")
        self.assertEqual(
            format_datetime(dt, format="%Y/%m/%d %H:%M"), "2021/07/06 12:30"
        )

        # 测试ISO格式字符串
        self.assertEqual(format_datetime("2021-07-06T12:30:00"), "2021-07-06 12:30")

        # 测试空值
        self.assertEqual(format_datetime(None), "未知时间")
        self.assertEqual(format_datetime(""), "未知时间")

        # 测试无效值
        self.assertEqual(format_datetime("invalid"), "未知时间")

    def test_format_date(self):
        # 测试date对象
        d = date(2021, 7, 6)
        self.assertEqual(format_date(d), "2021-07-06")
        self.assertEqual(format_date(d, format="%Y/%m/%d"), "2021/07/06")

        # 测试ISO格式字符串
        self.assertEqual(format_date("2021-07-06"), "2021-07-06")

        # 测试中文格式
        self.assertEqual(
            format_date(
                "2021年07月06日", format="%Y-%m-%d", input_format="%Y年%m月%d日"
            ),
            "2021-07-06",
        )

        # 测试空值
        self.assertEqual(format_date(None), "未知日期")
        self.assertEqual(format_date(""), "未知日期")

        # 测试无效值
        self.assertEqual(format_date("invalid"), "未知日期")
