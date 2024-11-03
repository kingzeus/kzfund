from flask_restx import Namespace, Resource, fields
from models.database import Database
from .common import response

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
        "account_id": fields.String(required=True, description="所属账户ID"),
        "name": fields.String(required=True, description="组合名称"),
        "description": fields.String(description="组合描述"),
        "is_default": fields.Boolean(description="是否为默认组合"),
    },
)


@api.route("/")
class PortfolioList(Resource):
    @api.doc("获取投资组合列表")
    @api.param("account_id", "账户ID")
    def get(self):
        """获取指定账户下的所有投资组合"""
        account_id = api.payload.get("account_id")
        if not account_id:
            return response(message="缺少账户ID", code=400)
        db = Database()
        return response(data=db.get_portfolios(account_id))

    @api.doc("创建新投资组合")
    @api.expect(portfolio_input)
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
        return response(
            data=db.get_portfolio(portfolio_id),
            message="组合创建成功",
        )


@api.route("/<string:id>")
@api.param("id", "组合ID")
class Portfolio(Resource):
    @api.doc("获取组合详情")
    def get(self, id):
        """获取指定组合的详情"""
        db = Database()
        portfolio = db.get_portfolio(id)
        if not portfolio:
            return response(message="组合不存在", code=404)
        return response(data=portfolio)

    @api.doc("更新组合信息")
    @api.expect(portfolio_input)
    def put(self, id):
        """更新组合信息"""
        data = api.payload
        db = Database()
        portfolio = db.update_portfolio(id, data)
        if not portfolio:
            return response(message="组合不存在", code=404)
        return response(data=portfolio, message="组合更新成功")

    @api.doc("删除组合")
    def delete(self, id):
        """删除组合"""
        db = Database()
        db.delete_portfolio(id)
        return response(message="组合删除成功")
