import logging
import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Any, Dict, List, Optional

from peewee import JOIN, fn
from playhouse.shortcuts import update_model_from_dict

from utils.datetime_helper import format_datetime

from .account import ModelAccount, ModelPortfolio
from .base import BaseModel, Database, db_connection
from .fund import ModelFund, ModelFundNav, ModelFundPosition, ModelFundTransaction
from .task import ModelTask

logger = logging.getLogger(__name__)


def init_database():
    """初始化数据库"""
    with db_connection():
        Database().get_db().create_tables(
            [
                ModelAccount,
                ModelPortfolio,
                ModelFundPosition,
                ModelFundTransaction,
                ModelFundNav,
                ModelFund,
                ModelTask,
            ]
        )


# 基金持仓相关操作
def get_fund_positions(portfolio_id: str) -> List[Dict[str, Any]]:
    """获取组合的基金持仓"""
    with db_connection():
        positions = ModelFundPosition.select().where(ModelFundPosition.portfolio == portfolio_id)

        if not positions:
            return []

        return [
            {
                "id": str(pos.id),
                "portfolio_id": str(pos.portfolio.id),
                "code": pos.code,
                "name": pos.name,
                "shares": float(pos.shares),
                "nav": float(pos.nav),
                "market_value": float(pos.market_value),
                "cost": float(pos.cost),
                "return_rate": float(pos.return_rate),
                "type": pos.type,
                "purchase_date": pos.purchase_date.isoformat(),
            }
            for pos in positions
        ]


def add_fund_position(data: Dict[str, Any]) -> str:
    """添加基金持仓"""
    with db_connection():
        position_id = str(uuid.uuid4())
        market_value = float(data["shares"]) * float(data["nav"])
        return_rate = (market_value - float(data["cost"])) / float(data["cost"])

        ModelFundPosition.create(
            id=position_id,
            portfolio=data["portfolio_id"],
            code=data["code"],
            name=data["name"],
            shares=data["shares"],
            nav=data["nav"],
            market_value=market_value,
            cost=data["cost"],
            return_rate=return_rate,
            type=data["type"],
            purchase_date=datetime.now(),
        )
        return position_id


def get_fund_transactions(portfolio_id: str) -> List[Dict[str, Any]]:
    """获取基金交易记录"""
    with db_connection():
        transactions = (
            ModelFundTransaction.select()
            .where(ModelFundTransaction.portfolio == portfolio_id)
            .order_by(ModelFundTransaction.transaction_date.desc())
        )

        if not transactions:
            return []

        return [
            {
                "id": str(trans.id),
                "portfolio_id": str(trans.portfolio.id),
                "code": trans.code,
                "type": trans.type,
                "shares": float(trans.shares),
                "amount": float(trans.amount),
                "nav": float(trans.nav),
                "fee": float(trans.fee),
                "transaction_date": trans.transaction_date.isoformat(),
            }
            for trans in transactions
        ]


def get_statistics() -> Dict[str, int]:
    """获取统计数据"""
    with db_connection():
        # 获取账户总数
        account_count = ModelAccount.select().count()  # pylint: disable=E1120

        # 获取组合总数
        portfolio_count = ModelPortfolio.select().count()  # pylint: disable=E1120

        # 获取基金总数
        fund_count = ModelFund.select().count()  # pylint: disable=E1120

        # 获取基金净值总数
        fund_nav_count = ModelFundNav.select().count()  # pylint: disable=E1120
        # 基金今日净值更新数量
        today_fund_nav_count = (
            ModelFundNav.select().where(ModelFundNav.nav_date == datetime.now().date()).count()
        )  # pylint: disable=E1120

        # 今天更新的基金净值数量
        today_update_fund_nav_count = (
            ModelFundNav.select().where(ModelFundNav.updated_at >= datetime.now().date()).count()
        )  # pylint: disable=E1120

        # 获取基金持仓总数
        position_count = ModelFundPosition.select().count()  # pylint: disable=E1120

        return {
            "account_count": account_count,  # 账户总数
            "portfolio_count": portfolio_count,  # 组合总数
            "fund_count": fund_count,  # 基金总数
            "fund_nav_count": fund_nav_count,  # 基金净值总数
            "today_fund_nav_count": today_fund_nav_count,  # 今日更新基金净值数量
            "today_update_fund_nav_count": today_update_fund_nav_count,  # 今天更新的基金净值数量
            "position_count": position_count,  # 基金持仓总数
        }


def get_transactions() -> List[Dict[str, Any]]:
    """获取所有交易记录"""
    with db_connection():
        try:
            transactions = (
                ModelFundTransaction.select(
                    ModelFundTransaction,
                    ModelPortfolio.name.alias("portfolio_name"),
                    ModelPortfolio.id.alias("portfolio_id"),
                    ModelFund.name.alias("fund_name"),
                )
                .join(ModelPortfolio)
                .join(ModelFund)
                .order_by(ModelFundTransaction.transaction_date.desc())
            )

            transactions_list = list(transactions)
            if not transactions_list:
                return []

            result = []
            for trans in transactions_list:
                try:
                    transaction_dict = {
                        "id": str(trans.id),
                        "portfolio_id": str(trans.portfolio.id),
                        "portfolio_name": trans.portfolio.name,
                        "fund_code": trans.fund.code,
                        "fund_name": trans.fund.name,
                        "type": trans.type,
                        "amount": f"¥ {float(trans.amount):,.2f}",
                        "shares": float(trans.shares),
                        "nav": float(trans.nav),
                        "fee": float(trans.fee),
                        "trade_time": format_datetime(trans.transaction_date),
                    }
                    result.append(transaction_dict)
                except Exception as e:
                    logger.error("Error processing transaction %s: %s", trans.id, str(e))

            return result

        except Exception as e:
            logger.error("获取交易记录失败: %s", str(e))
            return []


def add_transaction(
    portfolio_id: str,
    fund_code: str,
    transaction_type: str,
    amount: float,
    trade_time: datetime,
    nav: Optional[float] = None,
    shares: Optional[float] = None,
    fee: Optional[float] = 0.0,
) -> bool:
    """添加交易记录

    Args:
        portfolio_id: 投资组合ID
        fund_code: 基金代码
        transaction_type: 交易类型 (buy/sell)
        amount: 交易金额
        trade_time: 交易时间
        nav: 基金净值，可选
        shares: 份额，可选
        fee: 手续费，可选

    Returns:
        bool: 是否添加成功
    """
    try:
        with db_connection():
            # 1. 检查基金是否存在
            fund = ModelFund.get_or_none(ModelFund.code == fund_code)
            if not fund:
                # 如果基金不存在，触发更新基金详情任务
                from scheduler.job_manager import JobManager

                task_id = JobManager().add_task(
                    "fund_info",
                    fund_code=fund_code,
                )
                logger.info("已添加获取基金信息任务: %s", task_id)

            # 2. 如果没有提供份额和净值，则至少需要提供其中一个
            if nav is None and shares is None:
                raise ValueError("净值和份额不能同时为空")

            # 3. 计算缺失的值
            if nav is None and shares is not None:
                nav = amount / shares
            elif shares is None and nav is not None:
                shares = amount / nav

            # 4. 添加交易记录
            transaction = ModelFundTransaction.create(
                id=str(uuid.uuid4()),
                portfolio=portfolio_id,
                fund_code=fund_code,  # 确保使用正确的字段名
                type=transaction_type,
                amount=amount,
                shares=shares,
                nav=nav,
                fee=fee or 0.0,
                transaction_date=trade_time.date(),  # 只保存日期部分
            )

            # 5. 更新持仓信息
            if transaction:
                update_position_after_transaction(
                    portfolio_id=portfolio_id,
                    fund=fund or ModelFund(code=fund_code),  # 如果基金不存在，创建临时对象
                    transaction_type=transaction_type,
                    amount=amount,
                    shares=shares,
                    nav=nav,
                )

            return True
    except Exception as e:
        logger.error("添加交易记录失败: %s", str(e))
        return False


def update_transaction(
    transaction_id: str,
    portfolio_id: str,
    fund_code: str,
    transaction_type: str,
    amount: float,
    trade_time: datetime,
    fund_name: Optional[str] = None,
    nav: Optional[float] = None,
    shares: Optional[float] = None,
    fee: Optional[float] = 0.0,
) -> bool:
    """更新交易记录"""
    try:
        with db_connection():
            # 获取原交易记录
            old_transaction = ModelFundTransaction.get_by_id(transaction_id)

            # 更新交易记录
            old_transaction.portfolio = portfolio_id
            old_transaction.code = fund_code
            old_transaction.name = fund_name
            old_transaction.type = transaction_type
            old_transaction.amount = amount
            old_transaction.shares = shares or 0.0
            old_transaction.nav = nav or 0.0
            old_transaction.fee = fee
            old_transaction.transaction_date = trade_time
            old_transaction.save()

            # 重新计算持仓
            recalculate_position(portfolio_id, fund_code)

            return True
    except Exception as e:
        logger.error("更新交易记录失败: %s", str(e))
        return False


def update_position_after_transaction(
    portfolio_id: str,
    fund: ModelFund,
    transaction_type: str,
    amount: float,
    shares: float,
    nav: float,
) -> None:
    """更新交易后的持仓信息"""
    try:
        # 查找现有持仓
        position = (
            ModelFundPosition.select()
            .where(
                (ModelFundPosition.portfolio == portfolio_id)
                & (ModelFundPosition.code == fund.code)
            )
            .first()
        )

        if position:
            # 更新现有持仓
            if transaction_type == "buy":
                position.shares += shares
                position.cost += amount
            else:  # sell
                position.shares -= shares
                # 按比例减少成本
                position.cost *= (position.shares - shares) / position.shares

            position.nav = nav
            position.market_value = position.shares * nav
            if position.cost > 0:
                position.return_rate = (position.market_value - position.cost) / position.cost
            else:
                position.return_rate = 0

            if position.shares > 0:
                position.save()
            else:
                position.delete_instance()
        else:
            # 创建新持仓（仅限买入）
            if transaction_type == "buy":
                ModelFundPosition.create(
                    id=str(uuid.uuid4()),
                    portfolio=portfolio_id,
                    code=fund.code,
                    name=fund.name,
                    shares=shares,
                    nav=nav,
                    market_value=shares * nav,
                    cost=amount,
                    return_rate=0,
                    type="fund",
                    purchase_date=datetime.now(),
                )
    except Exception as e:
        logger.error("更新持仓失败: %s", str(e))


def recalculate_position(portfolio_id: str, fund_code: str) -> None:
    """重新计算基金持仓"""
    try:
        with db_connection():
            # 获取所有相关交易记录
            transactions = (
                ModelFundTransaction.select()
                .where(
                    (ModelFundTransaction.portfolio == portfolio_id)
                    & (ModelFundTransaction.code == fund_code)
                )
                .order_by(ModelFundTransaction.transaction_date.asc())
            )

            # 删除现有持仓
            ModelFundPosition.delete().where(
                (ModelFundPosition.portfolio == portfolio_id)
                & (ModelFundPosition.code == fund_code)
            ).execute()

            # 重新计算持仓
            total_shares = 0
            total_cost = 0
            latest_nav = 0
            fund_name = None

            for trans in transactions:
                if trans.type == "buy":
                    total_shares += trans.shares
                    total_cost += trans.amount
                else:  # sell
                    total_shares -= trans.shares
                    if total_shares > 0:
                        total_cost *= (total_shares - trans.shares) / total_shares
                latest_nav = trans.nav
                fund_name = trans.name

            # 如果还有持仓，创建新的持仓记录
            if total_shares > 0:
                market_value = total_shares * latest_nav
                return_rate = (market_value - total_cost) / total_cost if total_cost > 0 else 0

                ModelFundPosition.create(
                    id=str(uuid.uuid4()),
                    portfolio=portfolio_id,
                    code=fund_code,
                    name=fund_name,
                    shares=total_shares,
                    nav=latest_nav,
                    market_value=market_value,
                    cost=total_cost,
                    return_rate=return_rate,
                    type="fund",
                    purchase_date=datetime.now(),
                )
    except Exception as e:
        logger.error("重新计算持仓失败: %s", str(e))


def check_database_content():
    """检查数据库内容"""
    with db_connection():
        # 检查交易记录表
        trans_count = ModelFundTransaction.select().count()  # pylint: disable=E1120
        logger.info("交易记录数量: %s", trans_count)

        # 检查组合表
        portfolio_count = ModelPortfolio.select().count()  # pylint: disable=E1120
        logger.info("组合数量: %s", portfolio_count)

        # 如果有交易记录，打印第一条记录的详细信息
        if trans_count > 0:
            first_trans = ModelFundTransaction.select().first()  # pylint: disable=E1120
            logger.info(
                "第一条交易记录: %s",
                str(
                    {
                        "id": first_trans.id,
                        "portfolio": first_trans.portfolio.id,
                        "code": first_trans.code,
                        "type": first_trans.type,
                        "amount": first_trans.amount,
                        "shares": first_trans.shares,
                        "nav": first_trans.nav,
                        "fee": first_trans.fee,
                        "transaction_date": format_datetime(first_trans.transaction_date),
                    }
                ),
            )


########################################
# 通用函数
########################################
def get_record(model_class, search_fields: Dict[str, Any]) -> Optional[BaseModel]:
    """通用的获取记录函数

    Args:
        model_class: Peewee 模型类
        search_fields: 用于查找记录的字段和值的字典

    Example:
        get_record(
            ModelFundNav,
            {"fund_code": "000001", "nav_date": "2024-01-01"}
        )
    """
    try:
        with db_connection():
            return model_class.get_or_none(**search_fields)
    except Exception as e:
        logger.error("获取记录失败 - 模型: %s, 错误: %s", model_class.__name__, str(e))
        return None


def get_record_list(model_class, search_fields: Optional[Dict[str, Any]] = None) -> List[BaseModel]:
    """通用的获取记录列表函数

    Args:
        model_class: Peewee 模型类
        search_fields: 用于过滤记录的字段和值的字典,为空时返回所有记录

    Returns:
        List[BaseModel]: 记录列表

    Example:
        get_record_list(
            ModelFundNav,
            {"fund_code": "000001"}
        )
    """
    try:
        with db_connection():
            query = model_class.select()
            if search_fields:
                query = query.where(
                    *[
                        getattr(model_class, field) == value
                        for field, value in search_fields.items()
                    ]
                )
            return list(query)
    except Exception as e:
        logger.error("获取记录列表失败 - 模型: %s, 错误: %s", model_class.__name__, str(e))
        return []


def delete_record(
    model_class,
    search_fields: Dict[str, Any],
    callback_before: Optional[Callable[[BaseModel], None]] = None,
) -> bool:
    """通用的删除记录函数

    Args:
        model_class: Peewee 模型类
        search_fields: 用于查找记录的字段和值的字典
        callback_before: 删除记录前的回调函数
    Returns:
        bool: 删除是否成功

    Example:
        delete_record(
            ModelFundNav,
            {"fund_code": "000001", "nav_date": "2024-01-01"}
        )
    """
    try:
        with db_connection():
            record = model_class.get_or_none(**search_fields)
            if record:
                if callback_before:
                    callback_before(record)
                record.delete_instance()
                logger.info("成功删除记录 - 模型: %s, 条件: %s", model_class.__name__, str(search_fields))
                return True
            logger.warning("未找到要删除的记录 - 模型: %s, 条件: %s", model_class.__name__, str(search_fields))
            return False
    except Exception as e:
        logger.error(
            "删除记录失败 - 模型: %s, 条件: %s, 错误: %s",
            model_class.__name__,
            str(search_fields),
            str(e),
        )
        return False


def update_record(
    model_class,
    search_fields: Dict[str, Any],
    update_data: Dict[str, Any],
    callback_created: Optional[Callable[[BaseModel], None]] = None,
) -> bool:
    """通用的更新或创建记录函数

    Args:
        model_class: Peewee 模型类
        search_fields: 用于查找记录的字段和值的字典
        update_data: 需要更新的数据字典
        callback_created: 创建记录后的回调函数
    Example:
        _update_record(
            ModelFundNav,
            {"fund_code": "000001", "nav_date": "2024-01-01"},
            {"nav": 1.234, "acc_nav": 2.345}
        )
    """
    try:
        with db_connection():
            existing_record, created = model_class.get_or_create(
                **search_fields, defaults=update_data
            )
            if not created:
                update_model_from_dict(existing_record, update_data)
            existing_record.save()
            if created and callback_created:
                callback_created(existing_record)
            return True
    except Exception as e:
        logger.error("更新记录失败 - 模型: %s, 错误: %s", model_class.__name__, str(e))
        return False
