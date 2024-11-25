from peewee import (
    CharField,
    CompositeKey,
    DateField,
    DateTimeField,
    DecimalField,
    ForeignKeyField,
    TextField,
)

from .account import ModelPortfolio
from .base import BaseModel


class ModelFund(BaseModel):
    """基金基本信息模型"""

    # 基金代码，唯一标识符
    code = CharField(max_length=12, primary_key=True)
    # 基金简称
    name = CharField(max_length=100)
    # 基金全称
    full_name = CharField(max_length=255)
    # 基金类型
    type = CharField(max_length=20)
    # 发行日期
    issue_date = DateField()
    # 成立日期
    establishment_date = DateField()
    # 成立规模（单位：亿份）
    establishment_size = DecimalField(max_digits=20, decimal_places=4)
    # 基金管理公司
    company = CharField(max_length=100)
    # 基金托管人
    custodian = CharField(max_length=100)
    # 基金经理人
    fund_manager = CharField(max_length=100)
    # 管理费率
    management_fee = DecimalField(max_digits=10, decimal_places=4)
    # 托管费率
    custodian_fee = DecimalField(max_digits=10, decimal_places=4)
    # 销售服务费率
    sales_service_fee = DecimalField(max_digits=10, decimal_places=4)
    # 跟踪标的
    tracking = CharField(max_length=100)
    # 业绩比较基准
    performance_benchmark = CharField(max_length=100)

    # 投资范围
    investment_scope = TextField()
    # 投资目标
    investment_target = TextField()
    # 投资理念
    investment_philosophy = TextField()
    # 投资策略
    investment_strategy = TextField()
    # 分红政策
    dividend_policy = TextField()
    # 风险收益特征
    risk_return_characteristics = TextField()

    # 数据来源
    data_source = CharField(max_length=20)
    # 数据来源版本
    data_source_version = CharField(max_length=20)

    class Meta:
        table_name = "fund"

    def to_dict(self) -> dict:
        """将基金实例转换为可JSON序列化的字典"""
        result = super().to_dict()
        result.update(
            {
                "code": self.code,
                "name": self.name,
                "full_name": self.full_name,
                "type": self.type,
                "issue_date": self.issue_date.strftime("%Y-%m-%d") if self.issue_date else None,
                "establishment_date": (
                    self.establishment_date.strftime("%Y-%m-%d")
                    if self.establishment_date
                    else None
                ),
                "establishment_size": (
                    float(self.establishment_size) if self.establishment_size else None
                ),
                "company": self.company,
                "custodian": self.custodian,
                "fund_manager": self.fund_manager,
                "management_fee": float(self.management_fee) if self.management_fee else None,
                "custodian_fee": float(self.custodian_fee) if self.custodian_fee else None,
                "sales_service_fee": (
                    float(self.sales_service_fee) if self.sales_service_fee else None
                ),
                "tracking": self.tracking,
                "performance_benchmark": self.performance_benchmark,
                "investment_scope": self.investment_scope,
                "investment_target": self.investment_target,
                "investment_philosophy": self.investment_philosophy,
                "investment_strategy": self.investment_strategy,
                "dividend_policy": self.dividend_policy,
                "risk_return_characteristics": self.risk_return_characteristics,
                "data_source": self.data_source,
                "data_source_version": self.data_source_version,
            }
        )
        return result


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
    # 交易的基金，通过反向引用可以获取基金的所有交易记录
    fund = ForeignKeyField(ModelFund, backref="transactions", column_name="fund_code")
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


class ModelFundNav(BaseModel):
    """基金净值历史"""

    # 关联的基金，通过反向引用可以获取基金的所有净值历史
    fund = ForeignKeyField(ModelFund, backref="nav_history", column_name="fund_code")
    # 净值日期
    nav_date = DateField()
    # 基金单位净值
    nav = DecimalField(max_digits=10, decimal_places=4)
    # 累计净值
    acc_nav = DecimalField(max_digits=10, decimal_places=4)
    # 日收益率
    daily_return = DecimalField(max_digits=10, decimal_places=4, auto_round=True)
    # 申购状态
    subscription_status = CharField(max_length=20)
    # 赎回状态
    redemption_status = CharField(max_length=20)
    # 分红
    dividend = TextField(null=True)
    # 数据来源
    data_source = CharField(max_length=20)
    # 数据来源版本
    data_source_version = CharField(max_length=20)

    class Meta:
        table_name = "fund_nav_history"
        primary_key = CompositeKey("fund", "nav_date")

    def to_dict(self) -> dict:
        """将基金净值历史实例转换为可JSON序列化的字典"""
        result = super().to_dict()
        result.update(
            {
                "fund_code": self.fund_code,
                "nav_date": self.nav_date.strftime("%Y-%m-%d") if self.nav_date else None,
                "nav": float(self.nav) if self.nav else None,
                "acc_nav": float(self.acc_nav) if self.acc_nav else None,
                "daily_return": float(self.daily_return) if self.daily_return else None,
                "dividend": float(self.dividend) if self.dividend else None,
                "data_source": self.data_source,
                "data_source_version": self.data_source_version,
            }
        )
        return result
