from peewee import (
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKeyField,
)

from models.fund import ModelFund

from .account import ModelPortfolio
from .base import BaseModel


class ModelFundPosition(BaseModel):
    """基金持仓模型"""

    # 基金持仓的唯一标识符
    id = CharField(primary_key=True)
    # 关联的投资组合，通过反向引用可以获取组合的所有持仓
    portfolio = ForeignKeyField(ModelPortfolio, backref="positions")
    # 持仓的基金，通过反向引用可以获取基金的所有持仓记录
    fund = ForeignKeyField(ModelFund, backref="positions")
    # 持有的份额数量
    shares = DecimalField(max_digits=20, decimal_places=4)
    # 基金单位净值
    nav = DecimalField(max_digits=10, decimal_places=4)
    # 持仓市值（份额 * 净值）
    market_value = DecimalField(max_digits=20, decimal_places=2)
    # 持仓成本
    cost = DecimalField(max_digits=20, decimal_places=2)
    # 收益率（(市值 - 成本) / 成本）
    return_rate = DecimalField(max_digits=10, decimal_places=4)
    # 购买日期
    purchase_date = DateTimeField()

    class Meta:
        table_name = "fund_positions"
        db_name = "user"

    def to_dict(self) -> dict:
        """将基金持仓实例转换为可JSON序列化的字典"""
        result = super().to_dict()
        result.update(
            {
                "id": self.id,
                "portfolio_id": self.portfolio.id,
                "fund_code": self.fund.code,
                "shares": float(self.shares) if self.shares else None,
                "nav": float(self.nav) if self.nav else None,
                "market_value": float(self.market_value) if self.market_value else None,
                "cost": float(self.cost) if self.cost else None,
                "return_rate": float(self.return_rate) if self.return_rate else None,
                "purchase_date": self.purchase_date.isoformat() if self.purchase_date else None,
            }
        )
        return result


class ModelFundTransaction(BaseModel):
    """基金交易记录模型"""

    # 交易类型常量
    TYPE_BUY = "buy"
    TYPE_SELL = "sell"

    # 交易类型映射
    TRANSACTION_TYPES = {TYPE_BUY: "买入", TYPE_SELL: "卖出"}

    # 交易记录ID
    id = CharField(primary_key=True)
    # 所属投资组合，关联ModelPortfolio表
    portfolio = ForeignKeyField(ModelPortfolio, backref="transactions")
    # 基金代码
    fund_code = CharField(max_length=12, null=False)
    # 交易类型: buy(买入)/sell(卖出)
    type = CharField(max_length=20)
    # 交易份额，精确到小数点后4位
    shares = DecimalField(decimal_places=4, max_digits=20, null=False)
    # 交易金额，精确到小数点后2位，买入为正，卖出为负
    amount = DecimalField(decimal_places=2, max_digits=20, null=False)
    # 交易时净值，精确到小数点后4位
    nav = DecimalField(decimal_places=4, max_digits=10, null=False)
    # 交易手续费，精确到小数点后2位
    fee = DecimalField(decimal_places=2, max_digits=10, null=False)
    # 交易日期，格式：YYYY-MM-DD
    transaction_date = DateField(null=False)

    class Meta:
        table_name = "fund_transaction"
        db_name = "user"

    def to_dict(self) -> dict:
        """将交易记录转换为字典"""
        result = super().to_dict()
        result.update(
            {
                "id": self.id,
                "portfolio_id": self.portfolio.id,
                "fund_code": self.fund_code,
                "type": self.type,
                "type_name": self.TRANSACTION_TYPES.get(self.type, "未知"),
                "shares": float(self.shares),
                "amount": float(self.amount),
                "nav": float(self.nav),
                "fee": float(self.fee),
                "transaction_date": self.transaction_date.isoformat(),
            }
        )
        return result
