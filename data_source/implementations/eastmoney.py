import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import requests
import random
import string
import urllib.parse

from utils.datetime import format_date, get_timestamp
from utils.string_helper import extract_number_with_unit
from ..interface import IDataSource


logger = logging.getLogger(__name__)


class EastMoneyDataSource(IDataSource):
    """
    东方财富数据源实现
    版本 1.0.0:
    - 获取基金搜索建议
    - 获取基金基本信息
    - 获取基金详情






    """

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
        logger.debug("初始化东方财富数据源")

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
            logger.debug(f"请求基金搜索建议: {url}, params: {params}")

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            text = response.text
            if not text.startswith(params["callback"]):
                error_msg = "获取基金搜索建议失败"
                logger.error(error_msg)
                raise ValueError(error_msg)

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
            logger.debug(f"获取到 {len(results)} 个搜索建议")
            return results
        except Exception as e:
            logger.error(f"获取基金搜索建议失败: {str(e)}", exc_info=True)
            return []

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """获取基金基本信息"""
        try:
            url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
            params = {
                "rt": get_timestamp(),
            }
            logger.debug(f"请求基金信息: {url}, params: {params}")

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            text = response.text

            data = self._parse_jsonp_simple(text)
            if not data:
                error_msg = f"未找到基金: {fund_code}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            return {
                "code": fund_code,
                "name": data.get("name", ""),
                "net_value": data.get("dwjz", 0),  # 最新净值
                "net_value_date": data.get("jzrq", ""),  # 净值日期
                "valuation_time": data.get("gztime", ""),  # 估值时间
                "valuation_value": data.get("gsz", 0),  # 估值
                "valuation_growth": data.get("gszzl", 0),  # 估值增长率
            }
        except Exception as e:
            logger.error(f"获取基金信息失败: {str(e)}", exc_info=True)
            raise ValueError(f"获取基金信息失败: {str(e)}")

    def get_fund_detail(self, fund_code: str) -> Dict[str, Any]:
        """获取基金详情

        Args:
            fund_code: 基金代码

        Returns:
            包含基金详细信息的字典，包括:
            - fund_type: 基金类型
            - fund_scale: 基金规模
            - establishment_date: 成立日期
            等
        """
        try:
            url = f"https://fundf10.eastmoney.com/jbgk_{fund_code}.html"

            response = requests.get(url, headers=self.headers)
            response.raise_for_status()

            # 使用 BeautifulSoup 解析 HTML
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(response.text, "html.parser")

            # 获取表格数据
            table = soup.select_one("table.info")
            if not table:
                raise ValueError("未找到基金详情表格")

            fund_data = {}
            for row in table.select("tr"):
                # 获取该行所有的th和td元素
                cells = row.select("th, td")
                # 每两个单元格作为一组key-value
                for i in range(0, len(cells) - 1, 2):
                    key = cells[i].get_text(strip=True)
                    value = cells[i + 1].get_text(strip=True)
                    fund_data[key] = value
                    logger.debug(f"解析到基金详情: {key} = {value}")

            # 将原始数据映射到标准化的字段名
            return {
                "code": fund_code,
                "name": fund_data.get("基金简称"),
                "full_name": fund_data.get("基金全称"),
                "type": fund_data.get("基金类型"),
                "issue_date": format_date(
                    fund_data.get("发行日期"), input_format="%Y年%m月%d日"
                ),
                "establishment_date": format_date(
                    fund_data.get("成立日期/规模", "").split("/")[0],
                    input_format="%Y年%m月%d日",
                ),
                "establishment_size": extract_number_with_unit(
                    fund_data.get("成立日期/规模", "").split("/")[1], False
                ),
                "company": fund_data.get("基金管理人"),
                "custodian": fund_data.get("基金托管人"),
                "fund_manager": fund_data.get("基金经理人"),
                "management_fee": extract_number_with_unit(
                    fund_data.get("管理费率"), False, "percentage"
                ),
                "custodian_fee": extract_number_with_unit(
                    fund_data.get("托管费率"), False, "percentage"
                ),
                "sales_service_fee": extract_number_with_unit(
                    fund_data.get("销售服务费率", ""), False, "percentage"
                ),
                "tracking": fund_data.get("跟踪标的"),
                "performance_benchmark": fund_data.get("业绩比较基准"),
                "data_source": self.get_name(),
                "data_source_version": self.get_version(),
                # "investment_target": fund_data.get("投资目标", ""),
                # "investment_scope": fund_data.get("投资范围", ""),
            }

        except Exception as e:
            logger.error(f"获取基金详情失败: {str(e)}", exc_info=True)
            raise ValueError(f"获取基金详情失败: {str(e)}")

    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        # try:
        #     url = f"https://fundsuggest.eastmoney.com/LCAPI/FundNetValue/GetFundNetValueList"
        #     params = {
        #         "fundCode": fund_code,
        #         "pageIndex": 1,
        #         "pageSize": 50,  # 默认获取最近50条记录
        #     }

        #     if start_date:
        #         params["startDate"] = start_date.strftime("%Y-%m-%d")
        #     if end_date:
        #         params["endDate"] = end_date.strftime("%Y-%m-%d")

        #     logger.debug(f"请求基金历史净值: {url}, params: {params}")

        #     response = requests.get(url, params=params, headers=self.headers)
        #     response.raise_for_status()
        #     data = response.json()

        #     results = []
        #     if "Data" in data and "LSJZList" in data["Data"]:
        #         for item in data["Data"]["LSJZList"]:
        #             results.append(
        #                 {
        #                     "date": item.get("FSRQ", ""),
        #                     "nav": float(item.get("DWJZ", 0)),
        #                     "acc_nav": float(item.get("LJJZ", 0)),
        #                     "daily_return": float(item.get("JZZZL", 0))
        #                     / 100,  # 转换为小数
        #                 }
        #             )
        #     logger.debug(f"获取到 {len(results)} 条历史净值记录")
        #     return results
        # except Exception as e:
        #     logger.error(f"获取基金历史净值失败: {str(e)}", exc_info=True)
        #     raise ValueError(f"获取基金历史净值失败: {str(e)}")
        raise NotImplementedError
