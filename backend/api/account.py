from flask_restx import Namespace, Resource, fields

from kz_dash.backend.api.common import create_list_response_model, create_response_model
from models.account import ModelAccount, update_account
from kz_dash.models.database import delete_record, get_record, get_record_list, update_record
from kz_dash.utility.response import format_response
from kz_dash.utility.string_helper import get_uuid

api = Namespace("accounts", description="账户相关操作")

# 定义基础数据模型
account_base = api.model(
    "AccountBase",
    {
        "id": fields.String(required=True, description="账户ID"),
        "name": fields.String(required=True, description="账户名称"),
        "description": fields.String(description="账户描述"),
        "create_time": fields.DateTime(description="创建时间"),
        "update_time": fields.DateTime(description="更新时间"),
    },
)

# 使用通用函数创建响应模型
account_response = create_response_model(api, "Account", account_base)
account_list_response = create_list_response_model(api, "Account", account_base)

# 定义输入模型
account_input = api.model(
    "AccountInput",
    {
        "name": fields.String(required=True, description="账户名称"),
        "description": fields.String(description="账户描述"),
    },
)


@api.route("/")
class AccountList(Resource):
    @api.doc("获取所有账户")
    @api.marshal_with(account_list_response)
    def get(self):
        """获取所有账户列表"""
        return format_response(data=get_record_list(ModelAccount))

    @api.doc("创建新账户")
    @api.expect(account_input)
    @api.marshal_with(account_response)
    def post(self):
        """创建新账户"""
        data = api.payload
        account_id = update_account(get_uuid(), data)
        return format_response(data=get_record(ModelAccount, {"id": account_id}), message="账户创建成功")


@api.route("/<string:account_id>")
@api.param("account_id", "账户ID")
class Account(Resource):
    @api.doc("获取账户详情")
    @api.marshal_with(account_response)
    def get(self, account_id):
        """获取指定账户的详情"""
        account = get_record(ModelAccount, {"id": account_id})
        if not account:
            return format_response(message="账户不存在", code=404)
        return format_response(data=account)

    @api.doc("更新账户信息")
    @api.expect(account_input)
    @api.marshal_with(account_response)
    def put(self, account_id):
        """更新账户信息"""
        data = api.payload
        account = update_record(ModelAccount, {"id": account_id}, data)
        if not account:
            return format_response(message="账户不存在", code=404)
        return format_response(data=account, message="账户更新成功")

    @api.doc("删除账户")
    @api.marshal_with(account_response)
    def delete(self, account_id):
        """删除账户"""
        if delete_record(ModelAccount, {"id": account_id}):
            return format_response(message="账户删除成功")
        return format_response(message="账户不存在", code=404)
