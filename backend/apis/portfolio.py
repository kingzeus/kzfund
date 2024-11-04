from flask_restx import Namespace, Resource, fields
from models.database import (
    get_portfolios,
    add_portfolio,
    get_portfolio,
    update_portfolio,
    delete_portfolio,
)
from .common import response, create_response_model, create_list_response_model

api = Namespace("portfolios", description="投资组合相关操作")

# 定义基础数据模型
portfolio_base = api.model(
    "PortfolioBase",
    {
        "id": fields.String(required=True, description="组合ID"),
        "account_id": fields.String(required=True, description="所属账户ID"),
        "name": fields.String(required=True, description="组合名称"),
        "description": fields.String(description="组合描述"),
        "is_default": fields.Boolean(description="是否为默认组合"),
        "create_time": fields.DateTime(description="创建时间"),
        "update_time": fields.DateTime(description="更新时间"),
        "fund_count": fields.Integer(description="基金数量"),
        "total_market_value": fields.Float(description="总市值"),
    },
)

# 使用通用函数创建响应模型
portfolio_response = create_response_model(api, "Portfolio", portfolio_base)
portfolio_list_response = create_list_response_model(api, "Portfolio", portfolio_base)

# 定义输入模型
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
    @api.marshal_with(portfolio_list_response)
    def get(self):
        """获取指定账户下的所有投资组合"""
        account_id = api.payload.get("account_id")
        if not account_id:
            return response(message="缺少账户ID", code=400)
        return response(data=get_portfolios(account_id))

    @api.doc("创建新投资组合")
    @api.expect(portfolio_input)
    @api.marshal_with(portfolio_response)
    def post(self):
        """创建新投资组合"""
        data = api.payload
        portfolio_id = add_portfolio(
            data["account_id"],
            data["name"],
            data.get("description"),
            data.get("is_default", False),
        )
        return response(data=get_portfolio(portfolio_id), message="组合创建成功")


@api.route("/<string:id>")
@api.param("id", "组合ID")
class Portfolio(Resource):
    @api.doc("获取组合详情")
    @api.marshal_with(portfolio_response)
    def get(self, id):
        """获取指定组合的详情"""
        portfolio = get_portfolio(id)
        if not portfolio:
            return response(message="组合不存在", code=404)
        return response(data=portfolio)

    @api.doc("更新组合信息")
    @api.expect(portfolio_input)
    @api.marshal_with(portfolio_response)
    def put(self, id):
        """更新组合信息"""
        data = api.payload
        portfolio = update_portfolio(id, data)
        if not portfolio:
            return response(message="组合不存在", code=404)
        return response(data=portfolio, message="组合更新成功")

    @api.doc("删除组合")
    @api.marshal_with(portfolio_response)
    def delete(self, id):
        """删除组合"""
        delete_portfolio(id)
        return response(message="组合删除成功")
