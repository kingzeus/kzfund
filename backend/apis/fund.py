from flask_restx import Namespace, Resource, fields
from models.database import Database


api = Namespace("funds", description="基金相关操作")

# 定义数据模型
fund_position_model = api.model(
    "FundPosition",
    {
        "code": fields.String(required=True, description="基金代码"),
        "name": fields.String(required=True, description="基金名称"),
        "shares": fields.Float(required=True, description="持仓份额"),
        "nav": fields.Float(required=True, description="最新净值"),
        "market_value": fields.Float(required=True, description="持仓市值"),
        "cost": fields.Float(required=True, description="持仓成本"),
        "return_rate": fields.Float(required=True, description="收益率"),
        "type": fields.String(required=True, description="基金类型"),
        "purchase_date": fields.DateTime(required=True, description="购买日期"),
        "last_update": fields.DateTime(required=True, description="最后更新时间"),
    },
)


@api.route("/positions/<string:portfolio_id>")
@api.param("portfolio_id", "组合ID")
class FundPositionList(Resource):
    @api.doc("获取组合持仓")
    @api.marshal_list_with(fund_position_model)
    def get(self, portfolio_id):
        """获取指定组合的基金持仓"""
        db = Database()
        return db.get_fund_positions(portfolio_id)
