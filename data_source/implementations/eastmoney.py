import logging
import urllib.parse
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import execjs

import requests
from bs4 import BeautifulSoup

from data_source.interface import IDataSource
from scheduler.tasks.base import FundType
from utils.datetime_helper import format_date, get_timestamp, get_timestamp_ms
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
        return 24

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

    def get_fund_type(self, type: int) -> int:
        """转换基金类型"""
        if type == FundType.ALL:
            return 1
        elif type == FundType.STOCK:
            return 2
        elif type == FundType.MIXED:
            return 3
        elif type == FundType.INDEX:
            return 5
        elif type == FundType.QDII:
            return 6
        elif type == FundType.LOF:
            return 8
        elif type == FundType.BOND:
            return 13
        elif type == FundType.FOF:
            return 15
        return 0

    def get_fund_nav_list(
        self,
        page: int = 1,
        page_size: int = 200,
        type: int = 1,
    ) -> Dict[str, Any]:
        """获取基金最新净值列表

        Args:
            page: 页码,从1开始
            page_size: 每页数量
            type: 基金类型(1:全部 2:股票型 3:混合型 4:债券型 5:指数型 6:QDII 7:LOF 8:FOF)

        Returns:
            Dict: 基金净值列表
            - page: 页码
            - page_size: 每页数量
            - total: 总数量
            - items: 基金列表
                - code: 基金代码
                - name: 基金名称
                - nav: 当前净值
                - acc_nav: 累计净值
                - last_nav: 上一日净值
                - last_acc_nav: 上一日累计净值
                - daily_return: 日增长率
                - subscription_status: 申购状态
                - redemption_status: 赎回状态
        """
        try:
            url = "https://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx"
            params = {
                "t": 1,
                "onlySale": 0,
                "page": f"{page},{page_size}",
                "sort": "zdf,desc",
                "dt": get_timestamp_ms(),
                "lx": self.get_fund_type(type),
            }
            logger.debug("请求基金最新净值列表: %s, params: %s", url, params)

            response = requests.get(url, params=params, headers=self.headers)
            response.raise_for_status()

            # 解析返回的JavaScript对象
            text = response.text
            if not text.startswith("var db="):
                error_msg = "获取基金最新净值列表失败: 返回格式错误"
                logger.error(error_msg)
                raise ValueError(error_msg)

            # 构造JavaScript代码
            js_code = f"""
            {text}
            JSON.stringify(db);
            """

            # 执行JavaScript代码并获取结果
            # JSON.stringify + loads 方式
            # 优点:
            # 1. 通过 JSON 序列化保证了数据类型的一致性
            # 2. 跨平台/引擎行为更可预测
            # 缺点:
            # 1. 多了一次序列化和反序列化的开销
            ctx = execjs.compile(js_code)
            json_str = ctx.eval("JSON.stringify(db)")

            data = json.loads(json_str)
            print("解析到的数据: %s", data)
            results = {
                "page": data["curpage"],
                "page_size": page_size,
                "total": data["record"],
                "items": [],
            }

            for fund in data["datas"]:
                # 解析基金数据
                item = {
                    "nav_date": data["showday"][0],
                    "fund_code": fund[0],  # 基金代码 a
                    # "name": fund[1],  # 基金名称 b
                    # "pinyin":fund[2], # 拼音 c
                    "nav": float(fund[3]) if fund[3] else 0,  # 单位净值 d
                    "acc_nav": float(fund[4]) if fund[4] else 0,  # 累计净值 f
                    # "last_nav": float(fund[5]) if fund[5] else 0,  # 上一日净值 g
                    # "last_acc_nav": float(fund[6]) if fund[6] else 0,  # 上一日累计净值 h
                    "daily_return": (float(fund[8]) / 100 if fund[8] else 0),  # 日增长率 k
                    "subscription_status": fund[9],  # 申购状态 l
                    "redemption_status": fund[10],  # 赎回状态 m
                    "data_source": self.get_name(),
                    "data_source_version": self.get_version(),
                }
                results["items"].append(item)

            logger.debug("获取到 %d 条基金净值记录", len(data["datas"]))
            return results

        except Exception as e:
            logger.error("获取基金最新净值列表失败: %s", str(e), exc_info=True)
            raise ValueError(f"获取基金最新净值列表失败: {str(e)}")
