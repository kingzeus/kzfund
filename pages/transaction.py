from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import dash
from dash import html, dcc, Input, Output, State, callback
import feffery_antd_components as fac
from dash.exceptions import PreventUpdate
import logging

from models.database import (
    get_accounts,
    get_transactions,
    add_transaction,
    update_transaction,
    delete_transaction,
    get_portfolios,
)
from utils.datetime import format_datetime
from components.fund_code_aio import FundCodeAIO


# ============= 类型定义 =============
TransactionData = Dict[str, Any]
CascaderOption = Dict[str, Any]

# ============= 常量定义 =============
TRANSACTION_TYPES = [
    {"label": "买入", "value": "buy"},
    {"label": "卖出", "value": "sell"},
]

# ============= 样式常量 =============
PAGE_PADDING = 24
TABLE_STYLES = {"marginTop": "8px", "width": "100%"}
ICON_STYLES = {"fontSize": "24px", "marginRight": "8px"}
FORM_LAYOUT = {"labelCol": {"span": 6}, "wrapperCol": {"span": 18}}


# ============= 工具函数 =============
def create_operation_buttons(transaction_id: str) -> List[Dict[str, Any]]:
    """创建操作按钮配置

    Args:
        transaction_id: 交易记录ID

    Returns:
        按钮配置列表
    """
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


def build_cascader_options() -> List[CascaderOption]:
    """构建账户-组合级联选择器选项

    Returns:
        级联选择器选项列表
    """
    accounts = get_accounts()
    cascader_options = []

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

    return cascader_options


# ============= 组件渲染函数 =============
def render_transaction_table(initial_data: List[TransactionData]) -> fac.AntdCard:
    """渲染交易记录表格

    Args:
        initial_data: 初始交易数据列表

    Returns:
        交易记录表格卡片组件
    """
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
                style=TABLE_STYLES,
            ),
        ],
        bodyStyle={"padding": "12px"},
        style={"width": "100%"},
    )


def render_transaction_modal() -> fac.AntdModal:
    """渲染交易记录编辑对话框

    Returns:
        交易记录编辑对话框组件
    """
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
                labelCol=FORM_LAYOUT["labelCol"],
                wrapperCol=FORM_LAYOUT["wrapperCol"],
                children=[
                    fac.AntdFormItem(
                        fac.AntdCascader(
                            id="portfolio-cascader",
                            placeholder="请选择账户和组合",
                            options=[],
                            style={"width": "100%"},
                            changeOnSelect=False,
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
                            options=TRANSACTION_TYPES,
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
                            format="YYYY-MM-DD",
                            showTime=False,
                        ),
                        label="交易时间",
                        required=True,
                    ),
                ],
            )
        ],
    )


def render_delete_confirm_modal() -> fac.AntdModal:
    """渲染删除确认对话框

    Returns:
        删除确认对话框组件
    """
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


# ============= 页面主渲染函数 =============
def render_transaction_page() -> html.Div:
    """渲染交易记录页面

    Returns:
        页面主容器组件
    """
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
                                style=ICON_STYLES,
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
                    style={"padding": f"{PAGE_PADDING}px"},
                ),
            ),
            # 对话框组件
            render_transaction_modal(),
            render_delete_confirm_modal(),
        ],
        style={"padding": f"{PAGE_PADDING}px"},
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
    add_clicks: Optional[int],
    button_clicks: Optional[int],
    modal_ok_counts: Optional[int],
    delete_ok_counts: Optional[int],
    clicked_custom: Optional[Dict[str, Any]],
    store_data: List[TransactionData],
    portfolio_path: Optional[List[str]],
    fund_code: Optional[str],
    transaction_type: Optional[str],
    amount: Optional[float],
    trade_time: Optional[str],
    editing_id: Optional[str],
) -> Tuple[
    bool,
    str,
    List[CascaderOption],
    Optional[List[str]],
    str,
    Optional[str],
    Optional[float],
    Optional[str],
    bool,
    str,
    List[TransactionData],
]:
    """统一处理所有交易相关的操作

    处理:
    1. 新建交易
    2. 编辑交易
    3. 保存交易
    4. 删除交易

    Returns:
        包含各个组件状态的元组
    """
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

    try:
        # 处理新建交易按钮点击
        if trigger_id == "add-transaction-btn.nClicks":
            cascader_options = build_cascader_options()
            return (
                True,
                "新建交易",
                cascader_options,
                None,
                "",
                None,
                None,
                None,
                False,
                "",
                dash.no_update,
            )

        # 处理编辑按钮点击
        elif trigger_id == "transaction-list.nClicksButton":
            if not clicked_custom:
                return default_return

            action = clicked_custom.get("action")
            transaction_id = clicked_custom.get("id")
            transaction = next(
                (t for t in store_data if t["id"] == transaction_id), None
            )

            if not transaction:
                return default_return

            if action == "edit":
                cascader_options = build_cascader_options()
                # 找到当前交易记录对应的组合路径
                for account in cascader_options:
                    for portfolio in account["children"]:
                        if portfolio["value"] == transaction["portfolio_id"]:
                            cascader_value = [account["value"], portfolio["value"]]
                            return (
                                True,  # modal visible
                                "编辑交易记录",  # modal title
                                cascader_options,  # cascader options
                                cascader_value,  # cascader value
                                transaction["fund_code"],  # fund code
                                transaction["type"],  # transaction type
                                float(
                                    transaction["amount"]
                                    .replace("¥", "")
                                    .replace(",", "")
                                ),  # amount
                                transaction["trade_time"],  # trade time
                                False,  # delete modal visible
                                transaction_id,  # editing id
                                dash.no_update,  # store data
                            )

        # 处理保存交易
        elif trigger_id == "transaction-modal.okCounts":
            if not all(
                [portfolio_path, fund_code, transaction_type, amount, trade_time]
            ):
                return default_return

            portfolio_id = portfolio_path[-1] if portfolio_path else None
            if not portfolio_id:
                return default_return

            # 修改日期时间处理逻辑
            try:
                # 如果输入的是日期格式 (YYYY-MM-DD)
                if isinstance(trade_time, str) and len(trade_time) == 10:
                    trade_date = datetime.strptime(trade_time, "%Y-%m-%d")
                    trade_datetime = datetime.combine(trade_date, datetime.min.time())
                # 如果输入的是日期时间格式 (YYYY-MM-DD HH:MM:SS)
                else:
                    trade_datetime = datetime.strptime(trade_time, "%Y-%m-%d %H:%M:%S")
            except ValueError as e:
                logger.error(f"日期格式转换错误: {str(e)}", exc_info=True)
                return default_return

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
                    False,
                    dash.no_update,
                    [],
                    None,
                    "",
                    None,
                    None,
                    None,
                    False,
                    "",
                    get_transactions(),
                )

        # 处理删除确认
        elif trigger_id == "delete-confirm-modal.okCounts":
            if not editing_id:
                return default_return

            if delete_transaction(editing_id):
                return (
                    False,
                    dash.no_update,
                    [],
                    None,
                    "",
                    None,
                    None,
                    None,
                    False,
                    "",
                    get_transactions(),
                )

    except Exception as e:
        logger.error(f"处理交易操作失败: {str(e)}", exc_info=True)
        return default_return


@callback(
    Output("transaction-list", "data"),
    Input("transaction-store", "data"),
    prevent_initial_call=True,
)
def update_transaction_table(
    store_data: List[TransactionData],
) -> List[TransactionData]:
    """Store数据更新时，更新交易记录表格

    Args:
        store_data: 最新的交易数据列表

    Returns:
        更新后的表格数据
    """
    return store_data
