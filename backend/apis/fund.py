from flask_restx import Namespace, Resource, fields

from backend.apis.common import create_list_response_model, create_response_model
from models.database import (
    add_fund_position,
    delete_record,
    get_fund_positions,
    get_fund_transactions,
    update_record,
)
from models.fund_user import ModelFundPosition

from utils.response import format_response

api = Namespace("funds", description="基金相关操作")

# 定义基础数据模型
fund_position_base = api.model(
    "FundPositionBase",
    {
        "id": fields.String(required=True, description="持仓ID"),
        "portfolio_id": fields.String(required=True, description="组合ID"),
        "code": fields.String(required=True, description="基金代码"),
        "name": fields.String(required=True, description="基金名称"),
        "shares": fields.Float(required=True, description="持仓份额"),
        "nav": fields.Float(required=True, description="最新净值"),
        "market_value": fields.Float(required=True, description="持仓市值"),
        "cost": fields.Float(required=True, description="持仓成本"),
        "return_rate": fields.Float(required=True, description="收益率"),
        "type": fields.String(required=True, description="基金类型"),
        "purchase_date": fields.DateTime(required=True, description="购买日期"),
    },
)

fund_transaction_base = api.model(
    "FundTransactionBase",
    {
        "id": fields.String(required=True, description="交易ID"),
        "portfolio_id": fields.String(required=True, description="组合ID"),
        "code": fields.String(required=True, description="基金代码"),
        "type": fields.String(required=True, description="交易类型"),
        "shares": fields.Float(required=True, description="交易份额"),
        "amount": fields.Float(required=True, description="交易金额"),
        "nav": fields.Float(required=True, description="交易净值"),
        "fee": fields.Float(required=True, description="手续费"),
        "transaction_date": fields.DateTime(required=True, description="交易日期"),
    },
)

# 使用通用函数创建响应模型
position_response = create_response_model(api, "Position", fund_position_base)
position_list_response = create_list_response_model(api, "Position", fund_position_base)
transaction_list_response = create_list_response_model(api, "Transaction", fund_transaction_base)

# 定义输入模型
position_input = api.model(
    "PositionInput",
    {
        "portfolio_id": fields.String(required=True, description="组合ID"),
        "code": fields.String(required=True, description="基金代码"),
        "name": fields.String(required=True, description="基金名称"),
        "shares": fields.Float(required=True, description="持仓份额"),
        "nav": fields.Float(required=True, description="最新净值"),
        "cost": fields.Float(required=True, description="持仓成本"),
        "type": fields.String(required=True, description="基金类型"),
    },
)


@api.route("/positions/<string:portfolio_id>")
@api.param("portfolio_id", "组合ID")
class FundPositionList(Resource):
    @api.doc("获取组合持仓")
    @api.marshal_with(position_list_response)
    def get(self, portfolio_id):
        """获取指定组合的基金持仓"""
        return format_response(data=get_fund_positions(portfolio_id))

    @api.doc("添加基金持仓")
    @api.expect(position_input)
    @api.marshal_with(position_response)
    def post(self, portfolio_id):
        """添加基金持仓"""
        data = api.payload
        data["portfolio_id"] = portfolio_id
        add_fund_position(data)
        return format_response(data=get_fund_positions(portfolio_id), message="持仓添加成功")


@api.route("/positions/<string:position_id>")
@api.param("position_id", "持仓ID")
class FundPosition(Resource):
    @api.doc("更新持仓信息")
    @api.expect(position_input)
    @api.marshal_with(position_response)
    def put(self, position_id):
        """更新持仓信息"""
        data = api.payload
        position = update_record(ModelFundPosition, {"id": position_id}, data)
        if not position:
            return format_response(message="持仓不存在", code=404)
        return format_response(data=position, message="持仓更新成功")

    @api.doc("删除持仓")
    @api.marshal_with(position_response)
    def delete(self, position_id):
        """删除持仓"""
        if delete_record(ModelFundPosition, {"id": position_id}):
            return format_response(message="持仓删除成功")
        return format_response(message="持仓不存在", code=404)


@api.route("/transactions/<string:portfolio_id>")
@api.param("portfolio_id", "组合ID")
class FundTransactionList(Resource):
    @api.doc("获取交易记录")
    @api.marshal_with(transaction_list_response)
    def get(self, portfolio_id):
        """获取指定组合的交易记录"""
        return format_response(data=get_fund_transactions(portfolio_id))
