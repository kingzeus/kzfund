from peewee import CharField, ForeignKeyField, BooleanField
from .base import BaseModel

class Account(BaseModel):
    """账户模型"""

    id = CharField(primary_key=True)
    name = CharField(null=False)
    description = CharField(null=True)

    class Meta:
        table_name = "account"

class Portfolio(BaseModel):
    """投资组合模型"""

    id = CharField(primary_key=True)
    account = ForeignKeyField(Account, backref="portfolio")
    name = CharField(null=False)
    description = CharField(null=True)
    is_default = BooleanField(default=False)

    class Meta:
        table_name = "portfolio"
