from flask_restx import Namespace, Resource, fields
from models.database import Database


api = Namespace("portfolios", description="投资组合相关操作")

# 定义数据模型
portfolio_model = api.model(
    "Portfolio",
    {
        "id": fields.String(required=True, description="组合ID"),
        "account_id": fields.String(required=True, description="所属账户ID"),
        "name": fields.String(required=True, description="组合名称"),
        "description": fields.String(description="组合描述"),
        "is_default": fields.Boolean(description="是否为默认组合"),
        "create_time": fields.DateTime(description="创建时间"),
        "update_time": fields.DateTime(description="更新时间"),
        "total_market_value": fields.Float(description="总市值"),
        "fund_count": fields.Integer(description="基金数量"),
    },
)

portfolio_input = api.model(
    "PortfolioInput",
    {
        "name": fields.String(required=True, description="组合名称"),
        "description": fields.String(description="组合描述"),
        "is_default": fields.Boolean(description="是否为默认组合"),
    },
)


@api.route("/")
class PortfolioList(Resource):
    @api.doc("获取投资组合列表")
    @api.param("account_id", "账户ID")
    @api.marshal_list_with(portfolio_model)
    def get(self):
        """获取指定账户下的所有投资组合"""
        account_id = api.payload.get("account_id")
        db = Database()
        return db.get_portfolios(account_id)

    @api.doc("创建新投资组合")
    @api.expect(portfolio_input)
    @api.marshal_with(portfolio_model)
    def post(self):
        """创建新投资组合"""
        data = api.payload
        db = Database()
        portfolio_id = db.add_portfolio(
            data["account_id"],
            data["name"],
            data.get("description"),
            data.get("is_default", False),
        )
        return db.get_portfolio(portfolio_id)
