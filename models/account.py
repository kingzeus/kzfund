from peewee import BooleanField, CharField, ForeignKeyField

from models.base import BaseModel


class ModelAccount(BaseModel):
    """账户模型"""

    id = CharField(primary_key=True)
    name = CharField(null=False)
    description = CharField(null=True)

    class Meta:
        table_name = "account"

    def to_dict(self) -> dict:
        """将账户实例转换为可JSON序列化的字典"""
        result = super().to_dict()
        result.update({
            "id": self.id,
            "name": self.name,
            "description": self.description,
        })
        return result


class ModelPortfolio(BaseModel):
    """投资组合模型"""

    id = CharField(primary_key=True)
    account = ForeignKeyField(ModelAccount, backref="portfolio")
    name = CharField(null=False)
    description = CharField(null=True)
    is_default = BooleanField(default=False)

    class Meta:
        table_name = "portfolio"

    def to_dict(self) -> dict:
        """将投资组合实例转换为可JSON序列化的字典"""
        result = super().to_dict()
        result.update({
            "id": self.id,
            "account_id": self.account.id,
            "name": self.name,
            "description": self.description,
            "is_default": self.is_default,
        })
        return result
