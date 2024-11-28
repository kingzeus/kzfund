from typing import Any, Dict, Optional

from peewee import BooleanField, CharField, ForeignKeyField

from models.base import BaseModel
from utils.string_helper import get_uuid


class ModelAccount(BaseModel):
    """账户模型"""

    id = CharField(primary_key=True)
    name = CharField(null=False)
    description = CharField(null=True)

    class Meta:
        table_name = "account"
        db_name = "main"

    def to_dict(self) -> dict:
        """将账户实例转换为可JSON序列化的字典"""
        result = super().to_dict()
        result.update(
            {
                "id": self.id,
                "name": self.name,
                "description": self.description,
            }
        )
        return result


class ModelPortfolio(BaseModel):
    """投资组合模型"""

    id = CharField(primary_key=True)
    account = ForeignKeyField(ModelAccount, backref="portfolios")
    name = CharField(null=False)
    description = CharField(null=True)
    is_default = BooleanField(default=False)

    class Meta:
        table_name = "portfolio"
        db_name = "main"

    def to_dict(self) -> dict:
        """将投资组合实例转换为可JSON序列化的字典"""
        result = super().to_dict()
        result.update(
            {
                "id": self.id,
                "account_id": self.account.id,
                "name": self.name,
                "description": self.description,
                "is_default": self.is_default,
            }
        )
        return result


def update_account(account_id: Optional[str], data: Dict[str, Any]) -> bool:
    """更新账户信息"""
    from models.database import update_record

    if not account_id:
        account_id = get_uuid()

    def on_created(result):
        # 创建默认投资组合
        update_record(
            ModelPortfolio,
            {"id": get_uuid()},
            {
                "account_id": account_id,
                "name": f"{data['name']}-默认组合",
                "description": f"{data['name']}的默认投资组合",
                "is_default": True,
            },
        )
        print(f"账户创建完成: {result.to_dict()}")

    return update_record(ModelAccount, {"id": account_id}, data, on_created)


def delete_account(account_id: str) -> bool:
    """更新账户信息"""
    from models.database import delete_record, get_record_count

    def on_before(result):
        # 删除默认投资组合
        portfolio_count = get_record_count(ModelPortfolio, search_fields={"account_id": account_id})
        if portfolio_count > 0:
            raise ValueError("账户下存在投资组合，无法删除")

    return delete_record(ModelAccount, {"id": account_id}, on_before)
