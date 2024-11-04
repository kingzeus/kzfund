from peewee import CharField, DecimalField, ForeignKeyField, DateTimeField, CompositeKey
from .base import BaseModel
from .account import Portfolio

class FundPosition(BaseModel):
    """基金持仓模型"""

    id = CharField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, backref="positions")
    code = CharField(max_length=10)
    name = CharField(max_length=50)
    shares = DecimalField(max_digits=20, decimal_places=4)
    nav = DecimalField(max_digits=10, decimal_places=4)
    market_value = DecimalField(max_digits=20, decimal_places=2)
    cost = DecimalField(max_digits=20, decimal_places=2)
    return_rate = DecimalField(max_digits=10, decimal_places=4)
    type = CharField(max_length=20)
    purchase_date = DateTimeField()

    class Meta:
        table_name = "fund_positions"

class FundTransaction(BaseModel):
    """基金交易记录模型"""

    id = CharField(primary_key=True)
    portfolio = ForeignKeyField(Portfolio, backref="transactions")
    code = CharField(max_length=10)
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

    code = CharField(max_length=10)
    nav_date = DateTimeField()
    nav = DecimalField(max_digits=10, decimal_places=4)
    acc_nav = DecimalField(max_digits=10, decimal_places=4)
    daily_return = DecimalField(max_digits=10, decimal_places=4)
    dividend = DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        table_name = "fund_nav_history"
        primary_key = CompositeKey("code", "nav_date")
