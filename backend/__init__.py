from flask import Flask
from flask_restx import Api

from backend.api.account import api as account_ns
from backend.api.fund import api as fund_ns
from backend.api.portfolio import api as portfolio_ns
from kz_dash.backend.api.runtime import api as runtime_ns
from backend.api.task import api as task_ns
from config import API_CONFIG
from scheduler.job_manager import JobManager
from scheduler.tasks import init_tasks


def register_blueprint(app):
    # 初始化任务类型
    init_tasks()

    # 初始化任务管理器
    JobManager().init_app(app)

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
    api.add_namespace(runtime_ns, path="/api/runtime")
    api.add_namespace(task_ns, path="/api/task")
    api.init_app(app)
    return app
