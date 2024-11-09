import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import random
import string
import urllib.parse

from utils.datetime import get_timestamp
from ..interface import IDataSource


class EastMoneyDataSource(IDataSource):
    """东方财富数据源实现"""

    @classmethod
    def get_name(cls) -> str:
        return "eastmoney"

    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"

    def __init__(self):
        self.headers = {
            "Referer": "https://fund.eastmoney.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        }

    def _generate_random_string(self, length=20):
        # 定义字符集
        chars = string.digits
        # 生成随机字符串
        return "".join(random.choice(chars) for _ in range(length))

    def _parse_jsonp_simple(self, jsonp_str):
        """
        简单的JSONP解析方法
        """
        # 找到第一个'('和最后一个')'
        start = jsonp_str.find("(") + 1
        end = jsonp_str.rfind(")")

        if start > 0 and end > start:
            json_str = jsonp_str[start:end]
            return json.loads(json_str)
        return None

    def get_quick_tips(self, search_text: str) -> List[Dict[str, str]]:
        """获取基金搜索建议"""
        try:
            url = "https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx"
            params = {
                "callback": f"jQuery{self._generate_random_string()}_{get_timestamp()}",
                "m": "1",
                "key": urllib.parse.quote(search_text),
                "_": get_timestamp(),
            }
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            text = response.text
            if not text.startswith(params["callback"]):
                raise ValueError("获取基金搜索建议失败")

            data = self._parse_jsonp_simple(text)

            results = []
            if "Datas" in data:
                for item in data["Datas"]:
                    results.append(
                        {
                            "label": f"{item['NAME']} ({item['CODE']})",
                            "value": item["CODE"],
                        }
                    )
            return results
        except Exception as e:
            print(f"获取基金搜索建议失败: {str(e)}")
            return []

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """获取基金基本信息"""
        try:
            url = f"{self.base_url}/FundMApi/FundBaseTypeInformation.ashx"
            params = {
                "FCODE": fund_code,
                "deviceid": "123",  # 随机设备ID
                "plat": "Web",
                "product": "EFund",
                "version": "2.0.0",
            }
            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            if "Datas" in data:
                fund_data = data["Datas"]
                return {
                    "code": fund_code,
                    "name": fund_data.get("SHORTNAME", ""),
                    "type": fund_data.get("FTYPE", ""),
                    "company": fund_data.get("JJGS", ""),
                    "nav": float(fund_data.get("NAV", 0)),
                    "nav_date": fund_data.get("PDATE", ""),
                    "description": fund_data.get("COMMENTS", ""),
                }
            raise ValueError(f"未找到基金: {fund_code}")
        except Exception as e:
            raise ValueError(f"获取基金信息失败: {str(e)}")

    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        try:
            url = f"{self.base_url}/LCAPI/FundNetValue/GetFundNetValueList"
            params = {
                "fundCode": fund_code,
                "pageIndex": 1,
                "pageSize": 50,  # 默认获取最近50条记录
            }

            if start_date:
                params["startDate"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                params["endDate"] = end_date.strftime("%Y-%m-%d")

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()

            results = []
            if "Data" in data and "LSJZList" in data["Data"]:
                for item in data["Data"]["LSJZList"]:
                    results.append(
                        {
                            "date": item.get("FSRQ", ""),
                            "nav": float(item.get("DWJZ", 0)),
                            "acc_nav": float(item.get("LJJZ", 0)),
                            "daily_return": float(item.get("JZZZL", 0))
                            / 100,  # 转换为小数
                        }
                    )
            return results
        except Exception as e:
            raise ValueError(f"获取基金历史净值失败: {str(e)}")
