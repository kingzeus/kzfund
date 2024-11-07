from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import dash
from dash import html, dcc, Input, Output, State, callback
import feffery_antd_components as fac
from dash.exceptions import PreventUpdate

from models.database import (
    get_accounts,
    get_transactions,  # 需要在 models/database.py 中实现
    add_transaction,  # 需要在 models/database.py 中实现
    update_transaction,  # 需要在 models/database.py 中实现
    delete_transaction,  # 需要在 models/database.py 中实现
    get_portfolios,
)
from utils.datetime import format_datetime
from components.fund_code_aio import FundCodeAIO


def create_operation_buttons(transaction_id: str) -> List[Dict[str, Any]]:
    """创建操作按钮配置"""
    return [
        {
            "icon": "antd-edit",
            "iconRenderer": "AntdIcon",
            "type": "link",
            "custom": {
                "id": transaction_id,
                "action": "edit",
            },
        },
        {
            "icon": "antd-delete",
            "iconRenderer": "AntdIcon",
            "type": "link",
            "danger": True,
            "custom": {
                "id": transaction_id,
                "action": "delete",
            },
        },
    ]


def render_transaction_table(initial_data: List[Dict[str, Any]]) -> fac.AntdCard:
    """渲染交易记录表格"""
    return fac.AntdCard(
        title="交易记录",
        bordered=False,
        extra=[
            fac.AntdButton(
                "手工输入",
                type="primary",
                icon=fac.AntdIcon(icon="antd-plus"),
                id="add-transaction-btn",
            ),
        ],
        children=[
            fac.AntdTable(
                id="transaction-list",
                columns=[
                    {
                        "title": "交易ID",
                        "dataIndex": "id",
                        "key": "id",
                        "width": "15%",
                        "renderOptions": {"renderType": "copyable"},
                    },
                    {
                        "title": "组合",
                        "dataIndex": "portfolio_name",
                        "key": "portfolio_name",
                        "width": "10%",
                    },
                    {
                        "title": "基金代码",
                        "dataIndex": "fund_code",
                        "key": "fund_code",
                        "width": "10%",
                    },
                    {
                        "title": "基金名称",
                        "dataIndex": "fund_name",
                        "key": "fund_name",
                        "width": "15%",
                    },
                    # {
                    #     "title": "交易类型",
                    #     "dataIndex": "type",
                    #     "key": "type",
                    #     "width": "10%",
                    #     "renderOptions": {
                    #         "renderType": "tags",
                    #         "content": {
                    #             "buy": {"tag": "买入", "color": "green"},
                    #             "sell": {"tag": "卖出", "color": "red"},
                    #         },
                    #     },
                    # },
                    {
                        "title": "交易金额",
                        "dataIndex": "amount",
                        "key": "amount",
                        "width": "10%",
                    },
                    {
                        "title": "交易时间",
                        "dataIndex": "trade_time",
                        "key": "trade_time",
                        "width": "15%",
                    },
                    {
                        "title": "操作",
                        "dataIndex": "operation",
                        "key": "operation",
                        "width": "15%",
                        "renderOptions": {
                            "renderType": "button",
                        },
                    },
                ],
                data=initial_data,
                bordered=True,
                size="small",
                pagination={
                    "pageSize": 10,
                    "showSizeChanger": True,
                    "showQuickJumper": True,
                },
                style={
                    "marginTop": "8px",
                    "width": "100%",
                },
            ),
        ],
        bodyStyle={"padding": "12px"},
        style={"width": "100%"},
    )


def render_transaction_modal() -> fac.AntdModal:
    """渲染交易记录编辑对话框"""
    return fac.AntdModal(
        id="transaction-modal",
        title="新建交易",
        visible=False,
        maskClosable=False,
        width=600,
        renderFooter=True,
        okText="确定",
        cancelText="取消",
        children=[
            fac.AntdForm(
                id="transaction-form",
                labelCol={"span": 6},
                wrapperCol={"span": 18},
                children=[
                    fac.AntdFormItem(
                        fac.AntdCascader(
                            id="portfolio-cascader",
                            placeholder="请选择账户和组合",
                            options=[],
                            style={"width": "100%"},
                            changeOnSelect=False,  # 只允许选择叶子节点
                        ),
                        label="投资组合",
                        required=True,
                    ),
                    fac.AntdFormItem(
                        FundCodeAIO(aio_id="fund-code-aio"),
                        label="基金代码",
                        required=True,
                    ),
                    fac.AntdFormItem(
                        fac.AntdSelect(
                            id="transaction-type-select",
                            placeholder="请选择交易类型",
                            options=[
                                {"label": "买入", "value": "buy"},
                                {"label": "卖出", "value": "sell"},
                            ],
                            style={"width": "100%"},
                        ),
                        label="交易类型",
                        required=True,
                    ),
                    fac.AntdFormItem(
                        fac.AntdInputNumber(
                            id="amount-input",
                            placeholder="请输入交易金额",
                            style={"width": "100%"},
                            min=0,
                            precision=2,
                        ),
                        label="交易金额",
                        required=True,
                    ),
                    fac.AntdFormItem(
                        fac.AntdDatePicker(
                            id="trade-time-picker",
                            placeholder="请选择交易时间",
                            style={"width": "100%"},
                        ),
                        label="交易时间",
                        required=True,
                    ),
                ],
            )
        ],
    )


def render_delete_confirm_modal() -> fac.AntdModal:
    """渲染删除确认对话框"""
    return fac.AntdModal(
        id="delete-confirm-modal",
        title="确认删除",
        visible=False,
        children="确定要删除这条交易记录吗？删除后无法恢复。",
        okText="确定",
        cancelText="取消",
        renderFooter=True,
        maskClosable=False,
    )


def render_transaction_page() -> html.Div:
    """渲染交易记录页面"""
    initial_transactions = get_transactions()

    return html.Div(
        [
            # Store 组件
            dcc.Store(id="transaction-store", data=initial_transactions),
            dcc.Store(id="editing-transaction-id", data=""),
            # 页面标题
            fac.AntdRow(
                fac.AntdCol(
                    html.Div(
                        [
                            fac.AntdIcon(
                                icon="antd-calendar",
                                style={"fontSize": "24px", "marginRight": "8px"},
                            ),
                            "交易记录",
                        ],
                        style={
                            "fontSize": "20px",
                            "fontWeight": "bold",
                            "padding": "16px 0",
                            "display": "flex",
                            "alignItems": "center",
                        },
                    ),
                    span=24,
                )
            ),
            # 主要内容区域
            fac.AntdRow(
                fac.AntdCol(
                    render_transaction_table(initial_transactions),
                    span=24,
                    style={"padding": "8px"},
                ),
            ),
            # 对话框组件
            render_transaction_modal(),
            render_delete_confirm_modal(),
        ],
        style={"padding": "24px"},
    )


# ============= 回调函数 =============
@callback(
    [
        Output("transaction-modal", "visible"),
        Output("transaction-modal", "title"),
        Output("portfolio-cascader", "options"),
        Output("portfolio-cascader", "value"),
        Output(FundCodeAIO.ids.select("fund-code-aio"), "value"),
        Output("transaction-type-select", "value"),
        Output("amount-input", "value"),
        Output("trade-time-picker", "value"),
        Output("delete-confirm-modal", "visible"),
        Output("editing-transaction-id", "data"),
        Output("transaction-store", "data"),
    ],
    [
        Input("add-transaction-btn", "nClicks"),
        Input("transaction-list", "nClicksButton"),
        Input("transaction-modal", "okCounts"),
        Input("delete-confirm-modal", "okCounts"),
    ],
    [
        State("transaction-list", "clickedCustom"),
        State("transaction-store", "data"),
        State("portfolio-cascader", "value"),
        State(FundCodeAIO.ids.select("fund-code-aio"), "value"),
        State("transaction-type-select", "value"),
        State("amount-input", "value"),
        State("trade-time-picker", "value"),
        State("editing-transaction-id", "data"),
    ],
    prevent_initial_call=True,
)
def handle_transaction_actions(
    add_clicks,
    button_clicks,
    modal_ok_counts,
    delete_ok_counts,
    clicked_custom,
    store_data,
    portfolio_path,
    fund_code,
    transaction_type,
    amount,
    trade_time,
    editing_id,
):
    """统一处理所有交易相关的操作"""
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate

    trigger_id = ctx.triggered[0]["prop_id"]

    # 默认返回值
    default_return = (
        False,  # modal visible
        "新建交易",  # modal title
        [],  # cascader options
        None,  # cascader value
        "",  # fund code
        None,  # transaction type
        None,  # amount
        None,  # trade time
        False,  # delete modal visible
        "",  # editing id
        dash.no_update,  # store data
    )

    # 处理新建交易按钮点击
    if trigger_id == "add-transaction-btn.nClicks":
        accounts = get_accounts()  # 获取所有账户
        cascader_options = []

        # 构建级联选择器的选项
        for account in accounts:
            portfolios = get_portfolios(account["id"])
            portfolio_children = [
                {
                    "label": p["name"],
                    "value": p["id"],
                }
                for p in portfolios
            ]
            cascader_options.append(
                {
                    "label": account["name"],
                    "value": account["id"],
                    "children": portfolio_children,
                }
            )

        return (
            True,  # modal visible
            "新建交易",  # modal title
            cascader_options,  # cascader options
            None,  # cascader value
            "",  # fund code
            None,  # transaction type
            None,  # amount
            None,  # trade time
            False,  # delete modal visible
            "",  # editing id
            dash.no_update,  # store data
        )

    # 处理格按钮点击 - 编辑模式
    elif trigger_id == "transaction-list.nClicksButton":
        if not clicked_custom:
            return default_return

        action = clicked_custom.get("action")
        transaction_id = clicked_custom.get("id")
        transaction = next((t for t in store_data if t["id"] == transaction_id), None)

        if not transaction:
            return default_return

        if action == "edit":
            # 构建级联选择器的选项和当前值
            accounts = get_accounts()
            cascader_options = []
            cascader_value = None

            for account in accounts:
                portfolios = get_portfolios(account["id"])
                portfolio_children = []

                for p in portfolios:
                    portfolio_children.append(
                        {
                            "label": p["name"],
                            "value": p["id"],
                        }
                    )
                    # 找到当前交易记录对应的组合，设置级联值
                    if p["id"] == transaction["portfolio_id"]:
                        cascader_value = [account["id"], p["id"]]

                cascader_options.append(
                    {
                        "label": account["name"],
                        "value": account["id"],
                        "children": portfolio_children,
                    }
                )

            return (
                True,  # modal visible
                "编辑交易记录",  # modal title
                cascader_options,  # cascader options
                cascader_value,  # cascader value
                transaction["fund_code"],  # fund code
                transaction["type"],  # transaction type
                float(
                    transaction["amount"].replace("¥", "").replace(",", "")
                ),  # amount
                transaction["trade_time"],  # trade time
                False,  # delete modal visible
                transaction_id,  # editing id
                dash.no_update,  # store data
            )

    # 处理模态框确认 - 创建或更新交易记录
    elif trigger_id == "transaction-modal.okCounts":
        if not all([portfolio_path, fund_code, transaction_type, amount, trade_time]):
            return default_return

        # 从级联路径中获取组合ID（最后一个值）
        portfolio_id = portfolio_path[-1] if portfolio_path else None
        if not portfolio_id:
            return default_return

        # 转换交易时间字串为datetime对象
        trade_datetime = datetime.strptime(trade_time, "%Y-%m-%d %H:%M:%S")

        success = False
        if editing_id:
            success = update_transaction(
                transaction_id=editing_id,
                portfolio_id=portfolio_id,
                fund_code=fund_code,
                transaction_type=transaction_type,
                amount=amount,
                trade_time=trade_datetime,
            )
        else:
            success = add_transaction(
                portfolio_id=portfolio_id,
                fund_code=fund_code,
                transaction_type=transaction_type,
                amount=amount,
                trade_time=trade_datetime,
            )

        if success:
            return (
                False,  # modal visible
                dash.no_update,  # modal title
                [],  # cascader options
                None,  # cascader value
                "",  # fund code
                None,  # transaction type
                None,  # amount
                None,  # trade time
                False,  # delete modal visible
                "",  # editing id
                get_transactions(),  # store data
            )

    # 处理删除确认
    elif trigger_id == "delete-confirm-modal.okCounts":
        if not editing_id:
            return default_return

        if delete_transaction(editing_id):
            return (
                False,  # modal visible
                dash.no_update,  # modal title
                [],  # cascader options
                None,  # cascader value
                "",  # fund code
                None,  # transaction type
                None,  # amount
                None,  # trade time
                False,  # delete modal visible
                "",  # editing id
                get_transactions(),  # store data
            )

    return default_return


@callback(
    Output("transaction-list", "data"),
    Input("transaction-store", "data"),
    prevent_initial_call=True,
)
def update_transaction_table(store_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Store数据更新时，更新交易记录表格"""
    return store_data
