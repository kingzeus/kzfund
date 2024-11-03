from flask_restx import Namespace, Resource, fields
from models.database import Database


api = Namespace("accounts", description="账户相关操作")

# 定义数据模型
account_model = api.model(
    "Account",
    {
        "id": fields.String(required=True, description="账户ID"),
        "name": fields.String(required=True, description="账户名称"),
        "description": fields.String(description="账户描述"),
        "create_time": fields.DateTime(description="创建时间"),
        "update_time": fields.DateTime(description="更新时间"),
    },
)

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
    @api.marshal_list_with(account_model)
    def get(self):
        """获取所有账户列表"""
        db = Database()
        return db.get_accounts()

    @api.doc("创建新账户")
    @api.expect(account_input)
    @api.marshal_with(account_model)
    def post(self):
        """创建新账户"""
        data = api.payload
        db = Database()
        account_id = db.add_account(data["name"], data.get("description"))
        return db.get_account(account_id)


@api.route("/<string:id>")
@api.param("id", "账户ID")
class Account(Resource):
    @api.doc("获取账户详情")
    @api.marshal_with(account_model)
    def get(self, id):
        """获取指定账户的详情"""
        db = Database()
        return db.get_account(id)

    @api.doc("更新账户信息")
    @api.expect(account_input)
    @api.marshal_with(account_model)
    def put(self, id):
        """更新账户信息"""
        data = api.payload
        db = Database()
        return db.update_account(id, data)

    @api.doc("删除账户")
    def delete(self, id):
        """删除账户"""
        db = Database()
        db.delete_account(id)
        return "", 204
