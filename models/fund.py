from peewee import (
    CharField,
    DecimalField,
    ForeignKeyField,
    DateTimeField,
    DateField,
    TextField,
    CompositeKey,
)
from .base import BaseModel
from datetime import datetime
from .account import Portfolio


class Fund(BaseModel):
    """基金基本信息模型"""

    code = CharField(max_length=12, primary_key=True)
    name = CharField(max_length=100)  # 基金简称
    full_name = CharField(max_length=255)  # 基金全称
    type = CharField(max_length=20)  # 基金类型
    issue_date = DateField()  # 发行日期
    establishment_date = DateField()  # 成立日期
    establishment_size = DecimalField(
        max_digits=20, decimal_places=4
    )  # 成立规模(单位：亿份)
    company = CharField(max_length=100)  # 基金管理公司
    custodian = CharField(max_length=100)  # 基金托管人
    fund_manager = CharField(max_length=100)  # 基金经理人
    management_fee = DecimalField(max_digits=10, decimal_places=4)  # 管理费率
    custodian_fee = DecimalField(max_digits=10, decimal_places=4)  # 托管费率
    sales_service_fee = DecimalField(max_digits=10, decimal_places=4)  # 销售服务费率
    tracking = CharField(max_length=100)  # 跟踪标的
    performance_benchmark = CharField(max_length=100)  # 业绩比较基准

    investment_scope = TextField()  # 投资范围
    investment_target = TextField()  # 投资目标
    investment_philosophy = TextField()  # 投资理念
    investment_strategy = TextField()  # 投资策略
    dividend_policy = TextField()  # 分红政策
    risk_return_characteristics = TextField()  # 风险收益特征

    data_source = CharField(max_length=20)  # 数据来源
    data_source_version = CharField(max_length=20)  # 数据来源版本

    class Meta:
        table_name = "fund"


class FundPosition(BaseModel):
    """基金持仓模型"""

    id = CharField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, backref="positions")
    fund = ForeignKeyField(Fund, backref="positions")  # 修改为关联Fund模型
    shares = DecimalField(max_digits=20, decimal_places=4)
    nav = DecimalField(max_digits=10, decimal_places=4)
    market_value = DecimalField(max_digits=20, decimal_places=2)
    cost = DecimalField(max_digits=20, decimal_places=2)
    return_rate = DecimalField(max_digits=10, decimal_places=4)
    purchase_date = DateTimeField()

    class Meta:
        table_name = "fund_positions"


class FundTransaction(BaseModel):
    """基金交易记录模型"""

    id = CharField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, backref="transactions")
    fund = ForeignKeyField(Fund, backref="transactions")  # 修改为关联Fund模型
    type = CharField(max_length=20)
    shares = DecimalField(max_digits=20, decimal_places=4)
    amount = DecimalField(max_digits=20, decimal_places=2)
    nav = DecimalField(max_digits=10, decimal_places=4)
    fee = DecimalField(max_digits=10, decimal_places=2)
    transaction_date = DateTimeField()

    class Meta:
        table_name = "fund_transactions"


class FundNav(BaseModel):
    """基金净值历史"""

    fund = ForeignKeyField(Fund, backref="nav_history")  # 修改为关联Fund模型
    nav_date = DateTimeField()
    nav = DecimalField(max_digits=10, decimal_places=4)
    acc_nav = DecimalField(max_digits=10, decimal_places=4)
    daily_return = DecimalField(max_digits=10, decimal_places=4)
    dividend = DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        table_name = "fund_nav_history"
        primary_key = CompositeKey("fund", "nav_date")
