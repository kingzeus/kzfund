"""数据库表结构版本定义"""

SCHEMA_VERSIONS = {
    1: {
        "description": "初始版本 - 基础表结构",
        "changes": {
            "new_tables": [
                "accounts",
                "portfolios",
                "fund_transactions",
                "fund_positions",
                "fund_nav_history",
            ],
            "alter_tables": {},
            "drop_tables": [],
        },
        "schema": {
            "accounts": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "name": "VARCHAR(255) NOT NULL",
                    "description": "VARCHAR(255)",
                }
            },
            "portfolios": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "account_id": "VARCHAR(255) NOT NULL",
                    "name": "VARCHAR(255) NOT NULL",
                    "description": "VARCHAR(255)",
                    "is_default": "INTEGER NOT NULL",
                },
                "foreign_keys": {"account_id": "accounts(id)"},
                "indexes": ["account_id"],
            },
            "fund_transactions": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "portfolio_id": "VARCHAR(255) NOT NULL",
                    "code": "VARCHAR(10) NOT NULL",
                    "type": "VARCHAR(20) NOT NULL",
                    "shares": "DECIMAL(20, 4) NOT NULL",
                    "amount": "DECIMAL(20, 2) NOT NULL",
                    "nav": "DECIMAL(10, 4) NOT NULL",
                    "fee": "DECIMAL(10, 2) NOT NULL",
                    "transaction_date": "DATETIME NOT NULL",
                },
                "foreign_keys": {"portfolio_id": "portfolios(id)"},
                "indexes": ["portfolio_id", "code"],
            },
            "fund_positions": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "portfolio_id": "VARCHAR(255) NOT NULL",
                    "code": "VARCHAR(10) NOT NULL",
                    "name": "VARCHAR(50) NOT NULL",
                    "shares": "DECIMAL(20, 4) NOT NULL",
                    "nav": "DECIMAL(10, 4) NOT NULL",
                    "market_value": "DECIMAL(20, 2) NOT NULL",
                    "cost": "DECIMAL(20, 2) NOT NULL",
                    "return_rate": "DECIMAL(10, 4) NOT NULL",
                    "type": "VARCHAR(20) NOT NULL",
                    "purchase_date": "DATETIME NOT NULL",
                },
                "foreign_keys": {"portfolio_id": "portfolios(id)"},
                "indexes": ["portfolio_id", "code"],
            },
            "fund_nav_history": {
                "fields": {
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "code": "VARCHAR(10) NOT NULL",
                    "nav_date": "DATETIME NOT NULL",
                    "nav": "DECIMAL(10, 4) NOT NULL",
                    "acc_nav": "DECIMAL(10, 4) NOT NULL",
                    "daily_return": "DECIMAL(10, 4) NOT NULL",
                    "dividend": "DECIMAL(10, 4)",
                },
                "primary_key": ["code", "nav_date"],
                "indexes": ["code"],
            },
        },
    },
    2: {
        "description": "添加基金信息表，重构基金相关表的外键关系",
        "changes": {
            "new_tables": ["funds"],
            "alter_tables": {
                "fund_transactions": {"add_foreign_keys": {"code": "funds(code)"}},
                "fund_positions": {
                    "drop_columns": ["name", "type"],
                    "add_foreign_keys": {"code": "funds(code)"},
                },
                "fund_nav_history": {"add_foreign_keys": {"code": "funds(code)"}},
            },
            "drop_tables": [],
        },
        "schema": {
            "accounts": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "name": "VARCHAR(255) NOT NULL",
                    "description": "VARCHAR(255)",
                }
            },
            "portfolios": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "account_id": "VARCHAR(255) NOT NULL",
                    "name": "VARCHAR(255) NOT NULL",
                    "description": "VARCHAR(255)",
                    "is_default": "INTEGER NOT NULL",
                },
                "foreign_keys": {"account_id": "accounts(id)"},
                "indexes": ["account_id"],
            },
            "funds": {
                "fields": {
                    "code": "VARCHAR(10) NOT NULL PRIMARY KEY",
                    "name": "VARCHAR(100) NOT NULL",
                    "type": "VARCHAR(20) NOT NULL",
                    "company": "VARCHAR(100) NOT NULL",
                    "description": "VARCHAR(500)",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                }
            },
            "fund_transactions": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "portfolio_id": "VARCHAR(255) NOT NULL",
                    "code": "VARCHAR(10) NOT NULL",
                    "type": "VARCHAR(20) NOT NULL",
                    "shares": "DECIMAL(20, 4) NOT NULL",
                    "amount": "DECIMAL(20, 2) NOT NULL",
                    "nav": "DECIMAL(10, 4) NOT NULL",
                    "fee": "DECIMAL(10, 2) NOT NULL",
                    "transaction_date": "DATETIME NOT NULL",
                },
                "foreign_keys": {
                    "portfolio_id": "portfolios(id)",
                    "code": "funds(code)",
                },
                "indexes": ["portfolio_id", "code"],
            },
            "fund_positions": {
                "fields": {
                    "id": "VARCHAR(255) NOT NULL PRIMARY KEY",
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "portfolio_id": "VARCHAR(255) NOT NULL",
                    "code": "VARCHAR(10) NOT NULL",
                    "shares": "DECIMAL(20, 4) NOT NULL",
                    "nav": "DECIMAL(10, 4) NOT NULL",
                    "market_value": "DECIMAL(20, 2) NOT NULL",
                    "cost": "DECIMAL(20, 2) NOT NULL",
                    "return_rate": "DECIMAL(10, 4) NOT NULL",
                    "purchase_date": "DATETIME NOT NULL",
                },
                "foreign_keys": {
                    "portfolio_id": "portfolios(id)",
                    "code": "funds(code)",
                },
                "indexes": ["portfolio_id", "code"],
            },
            "fund_nav_history": {
                "fields": {
                    "created_at": "DATETIME NOT NULL",
                    "updated_at": "DATETIME NOT NULL",
                    "code": "VARCHAR(10) NOT NULL",
                    "nav_date": "DATETIME NOT NULL",
                    "nav": "DECIMAL(10, 4) NOT NULL",
                    "acc_nav": "DECIMAL(10, 4) NOT NULL",
                    "daily_return": "DECIMAL(10, 4) NOT NULL",
                    "dividend": "DECIMAL(10, 4)",
                },
                "primary_key": ["code", "nav_date"],
                "foreign_keys": {"code": "funds(code)"},
                "indexes": ["code"],
            },
        },
    },
}
