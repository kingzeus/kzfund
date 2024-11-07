from typing import List, Dict, Any, Optional
from datetime import datetime
from ..interface import IDataSource


class SimpleDataSource(IDataSource):
    """简单数据源实现"""
    
    @classmethod
    def get_name(cls) -> str:
        return "simple"
    
    @classmethod
    def get_version(cls) -> str:
        return "1.0.0"
    
    def __init__(self):
        # 模拟一些基金数据
        self._fund_data = {
            "000001": {
                "code": "000001",
                "name": "华夏成长混合",
                "type": "混合型",
                "company": "华夏基金",
                "nav": 1.234,
                "nav_date": "2024-03-20",
                "description": "本基金为混合型证券投资基金，主要投资于具有持续成长性的上市公司。",
            },
            "000002": {
                "code": "000002",
                "name": "华安安信消费混合",
                "type": "混合型",
                "company": "华安基金",
                "nav": 2.345,
                "nav_date": "2024-03-20",
                "description": "本基金为混合型基金，主要投资于消费行业的上市公司股票。",
            },
        }

    def get_quick_tips(self, search_text: str) -> List[Dict[str, str]]:
        """获取快速提示"""
        results = []
        for code, info in self._fund_data.items():
            if (
                search_text.lower() in code.lower()
                or search_text.lower() in info["name"].lower()
            ):
                results.append({"label": f"{info['name']} ({code})", "value": code})
        return results

    def get_fund_info(self, fund_code: str) -> Dict[str, Any]:
        """获取基金信息"""
        if fund_code not in self._fund_data:
            raise ValueError(f"未找到基金: {fund_code}")
        return self._fund_data[fund_code]

    def get_fund_nav_history(
        self,
        fund_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        if fund_code not in self._fund_data:
            raise ValueError(f"未找到基金: {fund_code}")

        # 模拟一些历史净值数据
        return [
            {
                "date": "2024-03-20",
                "nav": 1.234,
                "acc_nav": 2.345,
                "daily_return": 0.12,
            },
            {
                "date": "2024-03-19",
                "nav": 1.232,
                "acc_nav": 2.343,
                "daily_return": -0.08,
            },
        ]


