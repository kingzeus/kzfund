from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict
from .fund import FundPosition, FundTransaction


@dataclass
class Portfolio:
    """基金组合"""

    id: str  # 组合ID
    name: str  # 组合名称
    description: Optional[str]  # 组合描述
    create_time: datetime  # 创建时间
    update_time: datetime  # 更新时间
    positions: List[FundPosition]  # 持仓基金列表
    transactions: List[FundTransaction]  # 交易记录
    is_default: bool = False  # 是否为默认组合

    @property
    def total_market_value(self) -> Decimal:
        """计算组合总市值"""
        return sum(pos.market_value for pos in self.positions)

    @property
    def total_cost(self) -> Decimal:
        """计算组合总成本"""
        return sum(pos.cost for pos in self.positions)


@dataclass
class Account:
    """基金账户"""

    id: str  # 账户ID
    name: str  # 账户名称
    description: Optional[str]  # 账户描述
    create_time: datetime  # 创建时间
    update_time: datetime  # 更新时间
    portfolios: Dict[str, Portfolio]  # 基金组合字典，key为组合ID

    def get_default_portfolio(self) -> Optional[Portfolio]:
        """获取默认组合"""
        return next((p for p in self.portfolios.values() if p.is_default), None)

    @property
    def total_assets(self) -> Decimal:
        """计算账户总资产"""
        return sum(p.total_market_value for p in self.portfolios.values())
