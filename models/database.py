from typing import Dict, Optional, List
from datetime import datetime
from decimal import Decimal
from contextlib import contextmanager
import sqlite3
import uuid
from utils.singleton import Singleton
from config import DATABASE_CONFIG


@Singleton
class Database:
    """数据库管理类"""

    def __init__(self, db_path: str = DATABASE_CONFIG["path"]):
        self.db_path = db_path
        self.init_database()

    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(
            self.db_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
        )
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def init_database(self):
        """初始化数据库表结构"""
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # 账户表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS accounts (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    create_time TIMESTAMP NOT NULL,
                    update_time TIMESTAMP NOT NULL
                )
            """
            )

            # 基金组合表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS portfolios (
                    id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT,
                    is_default BOOLEAN NOT NULL DEFAULT 0,
                    create_time TIMESTAMP NOT NULL,
                    update_time TIMESTAMP NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            """
            )

            # 基金持仓表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS fund_positions (
                    id TEXT PRIMARY KEY,
                    portfolio_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    name TEXT NOT NULL,
                    shares DECIMAL NOT NULL,
                    nav DECIMAL NOT NULL,
                    market_value DECIMAL NOT NULL,
                    cost DECIMAL NOT NULL,
                    return_rate DECIMAL NOT NULL,
                    type TEXT NOT NULL,
                    purchase_date TIMESTAMP NOT NULL,
                    last_update TIMESTAMP NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            """
            )

            # 基金交易记录表
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS fund_transactions (
                    id TEXT PRIMARY KEY,
                    portfolio_id TEXT NOT NULL,
                    code TEXT NOT NULL,
                    date TIMESTAMP NOT NULL,
                    type TEXT NOT NULL,
                    shares DECIMAL NOT NULL,
                    amount DECIMAL NOT NULL,
                    nav DECIMAL NOT NULL,
                    fee DECIMAL NOT NULL,
                    FOREIGN KEY (portfolio_id) REFERENCES portfolios (id)
                )
            """
            )

            conn.commit()

    def add_account(self, name: str, description: Optional[str] = None) -> str:
        """添加账户"""
        account_id = str(uuid.uuid4())
        now = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO accounts (id, name, description, create_time, update_time)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account_id, name, description, now, now),
            )
            conn.commit()
        return account_id

    def get_accounts(self) -> List[Dict]:
        """获取所有账户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts ORDER BY create_time DESC")
            return [dict(row) for row in cursor.fetchall()]

    def get_account(self, account_id: str) -> Optional[Dict]:
        """获取指定账户的详情"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_account(self, account_id: str, data: Dict) -> Dict:
        """更新账户信息"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now = datetime.now()
            cursor.execute(
                """
                UPDATE accounts
                SET name = ?, description = ?, update_time = ?
                WHERE id = ?
                """,
                (data["name"], data.get("description"), now, account_id),
            )
            conn.commit()
            return self.get_account(account_id)

    def delete_account(self, account_id: str) -> None:
        """删除账户"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # 首先删除关联的组合
            cursor.execute("DELETE FROM portfolios WHERE account_id = ?", (account_id,))
            # 然后删除账户
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            conn.commit()

    def add_portfolio(
        self,
        account_id: str,
        name: str,
        description: Optional[str] = None,
        is_default: bool = False,
    ) -> str:
        """添加投资组合"""
        portfolio_id = str(uuid.uuid4())
        now = datetime.now()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO portfolios
                (id, account_id, name, description, is_default, create_time, update_time)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (portfolio_id, account_id, name, description, is_default, now, now),
            )
            conn.commit()
        return portfolio_id

    def get_portfolios(self, account_id: str) -> List[Dict]:
        """获取账户下的所有投资组合"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*,
                       COUNT(DISTINCT fp.code) as fund_count,
                       SUM(fp.market_value) as total_market_value
                FROM portfolios p
                LEFT JOIN fund_positions fp ON p.id = fp.portfolio_id
                WHERE p.account_id = ?
                GROUP BY p.id
                ORDER BY p.create_time DESC
                """,
                (account_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_portfolio(self, portfolio_id: str) -> Optional[Dict]:
        """获取指定组合的详情"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT p.*,
                       COUNT(DISTINCT fp.code) as fund_count,
                       SUM(fp.market_value) as total_market_value
                FROM portfolios p
                LEFT JOIN fund_positions fp ON p.id = fp.portfolio_id
                WHERE p.id = ?
                GROUP BY p.id
                """,
                (portfolio_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
