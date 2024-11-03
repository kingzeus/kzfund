from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional, List


@dataclass
class FundPosition:
    """基金持仓信息"""

    code: str  # 基金代码
    name: str  # 基金名称
    shares: Decimal  # 持仓份额
    nav: Decimal  # 最新净值
    market_value: Decimal  # 持仓市值
    cost: Decimal  # 持仓成本
    return_rate: Decimal  # 收益率
    type: str  # 基金类型：股票型、债券型、混合型、货币型
    purchase_date: datetime  # 购买日期
    last_update: datetime  # 最后更新时间


@dataclass
class FundNav:
    """基金净值信息"""

    code: str  # 基金代码
    date: datetime  # 日期
    nav: Decimal  # 单位净值
    acc_nav: Decimal  # 累计净值
    daily_return: Decimal  # 日收益率
    dividend: Optional[Decimal] = None  # 分红（如果有）


@dataclass
class FundTransaction:
    """基金交易记录"""

    code: str  # 基金代码
    date: datetime  # 交易日期
    type: str  # 交易类型：申购、赎回、分红再投资
    shares: Decimal  # 交易份额
    amount: Decimal  # 交易金额
    nav: Decimal  # 交易净值
    fee: Decimal  # 手续费


@dataclass
class FundPortfolio:
    """基金组合"""

    positions: List[FundPosition]  # 当前持仓
    transactions: List[FundTransaction]  # 历史交易

    @property
    def total_market_value(self) -> Decimal:
        """计算总市值"""
        return sum(pos.market_value for pos in self.positions)

    @property
    def total_cost(self) -> Decimal:
        """计算总成本"""
        return sum(pos.cost for pos in self.positions)

    @property
    def total_return(self) -> Decimal:
        """计算总收益"""
        return self.total_market_value - self.total_cost

    @property
    def total_return_rate(self) -> Decimal:
        """计算总收益率"""
        if self.total_cost == 0:
            return Decimal("0")
        return (self.total_return / self.total_cost) * Decimal("100")

    def get_position_by_type(self) -> dict:
        """按基金类型统计持仓"""
        type_stats = {}
        for pos in self.positions:
            if pos.type not in type_stats:
                type_stats[pos.type] = Decimal("0")
            type_stats[pos.type] += pos.market_value
        return type_stats

    def get_daily_returns(
        self, start_date: datetime, end_date: datetime
    ) -> List[tuple]:
        """获取指定时间段的每日收益"""
        # TODO: 实现每日收益计算逻辑
        pass
