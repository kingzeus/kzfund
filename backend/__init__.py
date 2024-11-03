from flask import Flask
from flask_restx import Api
from .apis.account import api as account_ns
from .apis.portfolio import api as portfolio_ns
from .apis.fund import api as fund_ns
from config import API_CONFIG


def register_blueprint(app):
    # 配置API
    api = Api(
        version=API_CONFIG["version"],
        title=API_CONFIG["title"],
        description=API_CONFIG["description"],
        doc=API_CONFIG["doc"],
    )

    # 注册命名空间
    api.add_namespace(account_ns, path="/api/accounts")
    api.add_namespace(portfolio_ns, path="/api/portfolios")
    api.add_namespace(fund_ns, path="/api/funds")

    api.init_app(app)
    return app
