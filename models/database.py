import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


from kz_dash.models.base import db_connection
from kz_dash.models.database import get_record_count
from kz_dash.utility.datetime_helper import format_datetime
from kz_dash.utility.string_helper import get_uuid

from .account import ModelAccount, ModelPortfolio

from .fund import ModelFund, ModelFundNav
from .fund_user import ModelFundPosition, ModelFundTransaction
from .task import ModelTask

logger = logging.getLogger(__name__)


# 基金持仓相关操作
def get_fund_positions(portfolio_id: str) -> List[Dict[str, Any]]:
    """获取组合的基金持仓"""
    with db_connection(db_name=ModelFundPosition._meta.db_name):
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
    with db_connection(db_name=ModelFundPosition._meta.db_name):
        position_id = get_uuid()
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
    with db_connection(db_name=ModelFundTransaction._meta.db_name):
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
    from scheduler.tasks import TaskStatus

    stats = {
        # main db
        "account_count": 0,  # 账户总数
        "portfolio_count": 0,  # 组合总数
        "fund_count": 0,  # 基金总数
        "fund_nav_count": 0,  # 基金净值总数
        "today_fund_nav_count": 0,  # 今日更新基金净值数量
        "today_update_fund_nav_count": 0,  # 今天更新的基金净值数量
        "position_count": 0,  # 基金持仓总数 todo: 需要优化
        # task db
        "today_task_count": 0,  # 今日任务总数
        "today_pending_task_count": 0,  # 今日待处理任务数量
        "today_failed_task_count": 0,  # 今日失败任务数量
    }
    today = datetime.now().date()

    # 使用单个连接处理 main 数据库的查询
    with db_connection(db_name="main"):
        stats.update(
            {
                "account_count": get_record_count(ModelAccount),
                "portfolio_count": get_record_count(ModelPortfolio),
                "fund_count": get_record_count(ModelFund),
                "fund_nav_count": get_record_count(ModelFundNav),
                "today_fund_nav_count": get_record_count(
                    ModelFundNav, search_fields={"nav_date": today}
                ),
                "today_update_fund_nav_count": get_record_count(
                    ModelFundNav, search_fields={"updated_at__gte": today}
                ),
                "position_count": get_record_count(ModelFundPosition),
            }
        )

    with db_connection(db_name="task"):
        stats.update(
            {
                "today_task_count": get_record_count(
                    ModelTask, search_fields={"updated_at__gte": today}
                ),
                "today_pending_task_count": get_record_count(
                    ModelTask,
                    search_fields={"status": TaskStatus.PENDING, "updated_at__gte": today},
                ),
                "today_failed_task_count": get_record_count(
                    ModelTask, search_fields={"status": TaskStatus.FAILED, "updated_at__gte": today}
                ),
            }
        )

    return stats


def get_transactions() -> List[Dict[str, Any]]:
    """获取所有交易记录"""
    with db_connection(db_name=ModelFundTransaction._meta.db_name):
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
                id=get_uuid(),
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
) -> bool:  # pylint: R0917
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
) -> None:  # pylint: R0917
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
                    id=get_uuid(),
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
                    id=get_uuid(),
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
