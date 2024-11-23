import logging
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from data_source.interface import IDataSource
from utils.datetime_helper import format_date, get_timestamp
from utils.string_helper import (
    extract_number_with_unit,
    generate_random_string,
    get_json_from_jsonp_simple,
)

logger = logging.getLogger(__name__)

# 请求超时时间（秒）
REQUEST_TIMEOUT = 10


class EastMoneyDataSource(IDataSource):
    """
    东方财富数据源实现
    版本 1.0.0:
    - 获取基金搜索建议
    - 获取基金基本信息
    - 获取基金详情
    - 获取基金历史净值数据





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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",  # pylint: disable=C0301
        }
        logger.debug("初始化东方财富数据源")

    def get_quick_tips(self, search_text: str) -> List[Dict[str, str]]:
        """获取基金搜索建议"""
        try:
            url = "https://fundsuggest.eastmoney.com/FundSearch/api/FundSearchAPI.ashx"
            params = {
                "callback": f"jQuery{generate_random_string()}_{get_timestamp()}",
                "m": "1",
                "key": urllib.parse.quote(search_text),
                "_": get_timestamp(),
            }
            logger.debug("请求基金搜索建议: %s, params: %s", url, params)

            response = requests.get(
                url, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()

            text = response.text
            if not text.startswith(params["callback"]):
                error_msg = "获取基金搜索建议失败"
                logger.error(error_msg)
                raise ValueError(error_msg)

            data = get_json_from_jsonp_simple(text)

            results = []
            if "Datas" in data:
                for item in data["Datas"]:
                    results.append(
                        {
                            "label": f"{item['NAME']} ({item['CODE']})",
                            "value": item["CODE"],
                        }
                    )
            logger.debug("获取到 %d 个搜索建议", len(results))
            return results
        except (KeyError, ValueError) as e:
            logger.error("解析基金搜索建议数据失败: %s", str(e), exc_info=True)
            return []
        except requests.exceptions.RequestException as e:
            logger.error("请求基金搜索建议失败: %s", str(e), exc_info=True)
            return []

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """获取基金基本信息"""
        try:
            url = f"https://fundgz.1234567.com.cn/js/{fund_code}.js"
            params = {
                "rt": get_timestamp(),
            }
            logger.debug("请求基金信息: %s, params: %s", url, params)

            response = requests.get(
                url, params=params, headers=self.headers, timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            text = response.text

            data = get_json_from_jsonp_simple(text)
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
        except (KeyError, ValueError) as e:
            logger.error("解析基金信息数据失败: %s", str(e), exc_info=True)
            raise ValueError(f"解析基金信息数据失败: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            logger.error("请求基金信息失败: %s", str(e), exc_info=True)
            raise ValueError(f"请求基金信息失败: {str(e)}") from e

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

            response = requests.get(url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()

            # 使用 BeautifulSoup 解析 HTML
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
                    logger.debug("解析到基金详情: %s = %s", key, value)

            # 将原始数据映射到标准化的字段名
            return {
                "code": fund_code,
                "name": fund_data.get("基金简称"),
                "full_name": fund_data.get("基金全称"),
                "type": fund_data.get("基金类型"),
                "issue_date": format_date(fund_data.get("发行日期"), input_format="%Y年%m月%d日"),
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

        except (KeyError, ValueError) as e:
            logger.error("解析基金详情数据失败: %s", str(e), exc_info=True)
            raise ValueError(f"解析基金详情数据失败: {str(e)}") from e
        except requests.exceptions.RequestException as e:
            logger.error("请求基金详情失败: %s", str(e), exc_info=True)
            raise ValueError(f"请求基金详情失败: {str(e)}") from e

    def get_fund_nav_history_size(self) -> int:
        """
        单词获取基金历史净值数据大小
        Returns:
            int: 历史净值数据大小
        """
        return 25

    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: str,
        end_date: str,
    ) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        try:
            url = "https://fundf10.eastmoney.com/F10DataApi.aspx"
            params = {
                "code": fund_code,
                "type": "lsjz",  # 历史净值
                "page": 1,  # 页码
                "sdate": start_date,
                "edate": end_date,
                "per": 20,  # 默认获取最近20条记录
            }
            logger.debug("请求基金历史净值: %s, params: %s", url, params)

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            # 解析返回的HTML内容
            text = response.text
            if not text.startswith("var apidata="):
                error_msg = "获取基金历史净值失败: 返回格式错误"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 提取总记录数
            records_start = text.find("records:") + 8
            records_end = text.find(",", records_start)
            total_records = int(text[records_start:records_end])
            logger.debug("总记录数: %s", total_records)

            if total_records == 0:
                logger.debug("未找到基金历史净值记录")
                return []

            if total_records > 20:
                error_msg = f"获取基金历史净值数量错误: {total_records}"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 提取HTML内容
            content_start = text.find('content:"') + 9
            content_end = text.find('",records:')
            html_content = text[content_start:content_end]
            html_content = html_content.replace("\\", "")

            # 使用BeautifulSoup解析HTML
            soup = BeautifulSoup(html_content, "html.parser")
            results = []

            # 遍历表格行
            for row in soup.select("tbody tr"):
                cols = row.select("td")
                if len(cols) >= 4:
                    # 提取日期和净值数据
                    date = cols[0].text.strip()
                    nav = float(cols[1].text.strip())
                    acc_nav = float(cols[2].text.strip())
                    subscription_status = cols[4].text.strip()
                    redemption_status = cols[5].text.strip()
                    dividend = cols[6].text.strip()

                    # 处理日增长率
                    daily_return_text = cols[3].text.strip().replace("%", "")
                    daily_return = float(daily_return_text) / 100 if daily_return_text else 0

                    item = {
                        "nav_date": date,
                        "nav": nav,
                        "acc_nav": acc_nav,
                        "daily_return": daily_return,
                        "subscription_status": subscription_status,
                        "redemption_status": redemption_status,
                        "data_source": self.get_name(),
                        "data_source_version": self.get_version(),
                    }
                    if dividend:
                        item["dividend"] = dividend
                    results.append(item)

            logger.debug("获取到 %d 条历史净值记录", len(results))
            return results

        except Exception as e:
            logger.error("获取基金历史净值失败: %s", str(e), exc_info=True)
            raise ValueError(f"获取基金历史净值失败: {str(e)}")
