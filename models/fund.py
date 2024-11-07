from peewee import CharField, DecimalField, ForeignKeyField, DateTimeField, CompositeKey
from .base import BaseModel
from .account import Portfolio

class Fund(BaseModel):
    """基金基本信息模型"""

    code = CharField(max_length=10, primary_key=True)
    name = CharField(max_length=100)
    type = CharField(max_length=20)  # 基金类型
    company = CharField(max_length=100)  # 基金公司
    description = CharField(max_length=500, null=True)  # 基金描述

    class Meta:
        table_name = "funds"


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
