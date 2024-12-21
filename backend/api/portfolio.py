import uuid

from flask_restx import Namespace, Resource, fields

from kz_dash.backend.api.common import create_list_response_model, create_response_model
from kz_dash.models.database import delete_record, get_record, get_record_list, update_record
from models.account import ModelPortfolio
from kz_dash.utility.response import format_response
from kz_dash.utility.string_helper import get_uuid

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
            return format_response(message="缺少账户ID", code=400)
        return format_response(data=get_record_list(ModelPortfolio, {"account_id": account_id}))

    @api.doc("创建新投资组合")
    @api.expect(portfolio_input)
    @api.marshal_with(portfolio_response)
    def post(self):
        """创建新投资组合"""
        data = api.payload
        portfolio_id = get_uuid()
        update_record(ModelPortfolio, {"id": portfolio_id}, data)

        return format_response(
            data=get_record(ModelPortfolio, {"id": portfolio_id}), message="组合创建成功"
        )


@api.route("/<string:portfolio_id>")
@api.param("portfolio_id", "组合ID")
class Portfolio(Resource):
    @api.doc("获取组合详情")
    @api.marshal_with(portfolio_response)
    def get(self, portfolio_id):
        """获取指定组合的详情"""
        portfolio = get_record(ModelPortfolio, {"id": portfolio_id})
        if not portfolio:
            return format_response(message="组合不存在", code=404)
        return format_response(data=portfolio)

    @api.doc("更新组合信息")
    @api.expect(portfolio_input)
    @api.marshal_with(portfolio_response)
    def put(self, portfolio_id):
        """更新组合信息"""
        data = api.payload
        portfolio = update_record(ModelPortfolio, {"id": portfolio_id}, data)
        if not portfolio:
            return format_response(message="更新失败", code=404)
        return format_response(data=portfolio, message="组合更新成功")

    @api.doc("删除组合")
    @api.marshal_with(portfolio_response)
    def delete(self, portfolio_id):
        """删除组合"""
        if delete_record(ModelPortfolio, {"id": portfolio_id}):
            return format_response(message="组合删除成功")
        return format_response(message="组合不存在", code=404)
