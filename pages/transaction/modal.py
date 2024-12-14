"""交易记录编辑弹窗模块

提供交易记录的创建和编辑功能:
- 渲染交易记录编辑弹窗
- 处理创建和编辑操作
- 表单验证和错误处理
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import dash
import feffery_antd_components as fac
from dash import Input, Output, State, callback
from dash.exceptions import PreventUpdate

from components.fund_code_aio import FundCodeAIO
from models.database import get_record, get_transactions, update_record
from models.fund import ModelFundNav
from models.fund_user import ModelFundTransaction
from scheduler.job_manager import JobManager
from kz_dash.utility.fac_helper import show_message
from kz_dash.utility.string_helper import get_uuid

from .utils import build_cascader_options

# ============= 日志配置 =============
logger = logging.getLogger(__name__)

# ============= 常量定义 =============
TRANSACTION_TYPE_OPTIONS = [
    {
        "label": ModelFundTransaction.TRANSACTION_TYPES[ModelFundTransaction.TYPE_BUY],
        "value": ModelFundTransaction.TYPE_BUY,
    },
    {
        "label": ModelFundTransaction.TRANSACTION_TYPES[ModelFundTransaction.TYPE_SELL],
        "value": ModelFundTransaction.TYPE_SELL,
    },
]

FEE_TYPE_OPTIONS = [
    {"label": "费率(%)", "value": "rate"},
    {"label": "金额(元)", "value": "fixed"},
]

FORM_LAYOUT = {
    "labelCol": {"flex": "none"},
    "wrapperCol": {"flex": "auto"},
    "labelAlign": "left",
}


# ============= 组件渲染函数 =============
def render_transaction_modal() -> fac.AntdModal:
    """渲染交易记录编辑弹窗

    Returns:
        AntdModal: 包含以下表单项的弹窗组件:
        - 投资组合选择器(级联选择)
        - 基金代码输入(自动完成)
        - 交易类型选择
        - 交易金额输入
        - 份额输入
        - 净值输入
        - 费用输入
        - 交易时间选择
    """
    return fac.AntdModal(
        id="transaction-modal",
        title="新建交易",
        visible=False,
        maskClosable=False,
        width=700,
        renderFooter=True,
        okText="确定",
        cancelText="取消",
        children=[
            fac.AntdForm(
                id="transaction-form",
                labelCol=FORM_LAYOUT["labelCol"],
                wrapperCol=FORM_LAYOUT["wrapperCol"],
                labelAlign=FORM_LAYOUT["labelAlign"],
                colon=False,
                children=[
                    # 基础信息分组
                    fac.AntdDivider(),
                    fac.AntdRow(
                        [
                            fac.AntdCol(
                                fac.AntdFormItem(
                                    fac.AntdCascader(
                                        id="portfolio-cascader",
                                        placeholder="请选择账户和组合",
                                        options=[],
                                        style={
                                            "width": "100%",
                                        },
                                        changeOnSelect=False,
                                    ),
                                    label="投资组合",
                                    required=True,
                                ),
                                style={"marginBottom": "-18px"},
                                span=8,
                            ),
                            fac.AntdCol(
                                style={"marginBottom": "-18px"},
                                span=8,
                            ),
                            fac.AntdCol(
                                fac.AntdFormItem(
                                    fac.AntdRadioGroup(
                                        id="transaction-type-select",
                                        options=TRANSACTION_TYPE_OPTIONS,
                                        optionType="button",
                                        defaultValue="None",
                                        style={
                                            "width": "100%",
                                        },
                                    ),
                                    label="交易类型",
                                    required=True,
                                ),
                                style={"marginBottom": "-18px"},
                                span=8,
                            ),
                        ],
                        gutter=30,
                        justify="space-between",
                    ),
                    fac.AntdDivider(isDashed=True, style={"margin": "12px"}),
                    # 交易信息分组
                    fac.AntdRow(
                        [
                            fac.AntdCol(
                                [
                                    fac.AntdFormItem(
                                        FundCodeAIO(aio_id="fund-code-aio"),
                                        label="基金代码",
                                        required=True,
                                        style={"marginBottom": "0"},
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
                                        style={"marginBottom": "0"},
                                    ),
                                    fac.AntdFormItem(
                                        fac.AntdInputNumber(
                                            id="nav-input",
                                            placeholder="请输入净值",
                                            style={"width": "100%"},
                                            min=0,
                                            precision=4,
                                        ),
                                        label="单位净值",
                                        required=True,
                                        style={"marginBottom": "0"},
                                    ),
                                ],
                                span=8,
                            ),
                            fac.AntdCol(
                                fac.AntdFormItem(
                                    fac.AntdInputNumber(
                                        prefix=fac.AntdIcon(icon="antd-money-collect"),
                                        id="amount-input",
                                        placeholder="交易金额",
                                        style={
                                            "width": "100%",
                                            "height": "100px",
                                            "fontSize": "80px",
                                        },
                                        className={
                                            "#amount-input": {
                                                "fontSize": "48px",
                                                "fontWeight": "500",
                                            }
                                        },
                                        min=0,
                                        precision=2,
                                        bordered=False,
                                        controls=False,
                                    ),
                                    required=True,
                                ),
                                span=12,
                            ),
                        ],
                    ),
                    # 详细信息分组
                    fac.AntdRow(
                        [
                            fac.AntdCol(
                                span=8,
                                style={"paddingRight": "12px"},
                            ),
                            fac.AntdCol(
                                fac.AntdFormItem(
                                    fac.AntdInputNumber(
                                        id="shares-input",
                                        placeholder="请输入份额",
                                        style={"width": "100%"},
                                        min=0,
                                        precision=4,
                                    ),
                                    label="份额",
                                ),
                                span=8,
                                style={"paddingRight": "12px"},
                            ),
                            fac.AntdCol(
                                fac.AntdFormItem(
                                    fac.AntdSpace(
                                        [
                                            fac.AntdSelect(
                                                id="fee-type-select",
                                                options=FEE_TYPE_OPTIONS,
                                                defaultValue="rate",
                                                allowClear=False,
                                                style={"width": "120px"},
                                            ),
                                            fac.AntdInputNumber(
                                                id="fee-input",
                                                placeholder="请输入费用",
                                                style={"width": "calc(100% - 120px)"},
                                                min=0,
                                                precision=2,
                                                addonAfter="%",
                                            ),
                                        ],
                                        direction="horizontal",
                                        style={"width": "100%"},
                                    ),
                                    label="费用",
                                ),
                                span=12,
                            ),
                        ],
                    ),
                ],
            )
        ],
    )


# ============= 回调函数 =============
@callback(
    [
        Output("transaction-modal", "visible", allow_duplicate=True),
        Output("transaction-modal", "title", allow_duplicate=True),
        Output("portfolio-cascader", "options", allow_duplicate=True),
        Output("portfolio-cascader", "value", allow_duplicate=True),
        Output(FundCodeAIO.ids.select("fund-code-aio"), "value", allow_duplicate=True),
        Output("transaction-type-select", "value", allow_duplicate=True),
        Output("amount-input", "value", allow_duplicate=True),
        Output("shares-input", "value", allow_duplicate=True),
        Output("nav-input", "value", allow_duplicate=True),
        Output("fee-input", "value", allow_duplicate=True),
        Output("trade-time-picker", "value", allow_duplicate=True),
        Output("editing-transaction-id", "data", allow_duplicate=True),
    ],
    [
        Input("add-transaction-btn", "nClicks"),
        Input("nav-input", "nSubmit"),
        Input("amount-input", "nSubmit"),
    ],
    [State("nav-input", "value"), State("amount-input", "value")],
    prevent_initial_call=True,
)
def show_transaction_modal(
    n_clicks: Optional[int],
    nav_submit: Optional[int],
    amount_submit: Optional[int],
    nav: Optional[float],
    amount: Optional[float],
) -> Tuple:
    """显示新建交易对话框并处理自动计算"""
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]

    # 如果是净值或金额输入触发
    if triggered_id in ["nav-input", "amount-input"]:
        if nav and amount:
            try:
                shares = round(amount / nav, 4)
                return (
                    dash.no_update,  # modal visible
                    dash.no_update,  # modal title
                    dash.no_update,  # cascader options
                    dash.no_update,  # cascader value
                    dash.no_update,  # fund code
                    dash.no_update,  # transaction type
                    dash.no_update,  # amount
                    shares,  # shares - 更新计算的份额
                    dash.no_update,  # nav
                    dash.no_update,  # fee
                    dash.no_update,  # trade time
                    dash.no_update,  # editing id
                )
            except:
                return tuple([dash.no_update] * 12)

    # 如果是添加按钮触发
    if triggered_id == "add-transaction-btn" and n_clicks:
        cascader_options = build_cascader_options()
        today = datetime.now().strftime("%Y-%m-%d")
        return (
            True,  # modal visible
            "新建交易",  # modal title
            cascader_options,  # cascader options
            None,  # cascader value
            "",  # fund code
            None,  # transaction type
            None,  # amount
            None,  # shares
            None,  # nav
            None,  # fee
            today,  # trade time - 默认今天
            "",  # editing id
        )

    raise PreventUpdate


@callback(
    [
        Output("transaction-store", "data", allow_duplicate=True),
        Output("transaction-modal", "visible", allow_duplicate=True),
    ],
    Input("transaction-modal", "okCounts"),
    [
        State("portfolio-cascader", "value"),
        State(FundCodeAIO.ids.select("fund-code-aio"), "value"),
        State("transaction-type-select", "value"),
        State("amount-input", "value"),
        State("shares-input", "value"),
        State("nav-input", "value"),
        State("fee-type-select", "value"),
        State("fee-input", "value"),
        State("trade-time-picker", "value"),
        State("editing-transaction-id", "data"),
    ],
    prevent_initial_call=True,
)
def handle_transaction_save(
    ok_counts: Optional[int],
    portfolio_path: Optional[List[str]],
    fund_code: Optional[str],
    transaction_type: Optional[str],
    amount: Optional[float],
    shares: Optional[float],
    nav: Optional[float],
    fee_type: Optional[str],
    fee: Optional[float],
    trade_time: Optional[str],
    editing_id: Optional[str],
) -> Tuple[List[Dict[str, Any]], bool]:
    """处理交易记录保存"""
    # 验证必填字段
    if not ok_counts or not all([portfolio_path, fund_code, transaction_type, amount, trade_time]):
        raise PreventUpdate

    try:
        # 获取组合ID
        portfolio_id = portfolio_path[-1] if portfolio_path else None
        if not portfolio_id:
            raise PreventUpdate

        # 处理日期时间

        if not trade_time:
            logger.error("无效的交易时间格式")
            raise PreventUpdate

        # 保存交易记录

        # 交易记录数据
        transaction_data = {
            "portfolio": portfolio_id,
            "fund_code": fund_code,
            "type": transaction_type,
            "amount": amount,
            "shares": shares or 0.0,
            "nav": nav or 0.0,
            "fee": fee or 0.0,
            "fee_type": fee_type,
            "transaction_date": trade_time,
        }

        condition = {"id": editing_id if editing_id else get_uuid()}
        success = update_record(ModelFundTransaction, condition, transaction_data)

        if success:
            return get_transactions(), False
        logger.error("保存交易记录失败")

    except Exception as e:
        logger.error("处理交易保存失败: %s", str(e), exc_info=True)

    return dash.no_update, dash.no_update


@callback(
    Output("fee-input", "addonAfter"),
    Input("fee-type-select", "value"),
    prevent_initial_call=False,
)
def update_fee_input_suffix(fee_type: str) -> str:
    """更新费用输入框后缀

    Args:
        fee_type: 费用类型，'rate' 或 'fixed'

    Returns:
        str: 输入框后缀，'%' 或 '元'
    """
    if fee_type == "rate":
        return "%"
    return "元"


@callback(
    Output("fee-input", "value", allow_duplicate=True),
    [
        Input("amount-input", "nSubmit"),
        Input("fee-type-select", "value"),
    ],
    [
        State("amount-input", "value"),
        State("fee-input", "value"),
    ],
    prevent_initial_call=True,
)
def calculate_fee(
    amount_submit: Optional[int],
    fee_type: str,
    amount: Optional[float],
    current_fee: Optional[float],
) -> Optional[float]:
    """计算费用

    根据费用类型和交易金额自动计算费用：
    - 费率: 费用 = 金额 * 费率%
    - 固定金额: 保持不变
    """
    if not amount or not fee_type:
        return dash.no_update

    try:
        if fee_type == "rate" and current_fee:
            # 如果是费率，自动计算费用金额
            fee_amount = amount * (current_fee / 100)
            return round(fee_amount, 2)
        return current_fee

    except Exception as e:
        logger.error("计算费用失败: %s", str(e))

    return dash.no_update


@callback(
    Output("nav-input", "value", allow_duplicate=True),
    [
        Input(FundCodeAIO.ids.select("fund-code-aio"), "value"),
        Input("trade-time-picker", "value"),
    ],
    prevent_initial_call=True,
)
def update_nav_value(fund_code: Optional[str], trade_time: Optional[str]) -> Optional[float]:
    """更新净值输入框的值

    当基金代码和交易时间都有值时，自动获取对应日期的净值
    """
    if not fund_code or not trade_time:
        raise PreventUpdate

    try:
        # 1. 从数据库中获取基金净值
        nav: Optional[ModelFundNav] = get_record(
            ModelFundNav, {"fund_code": fund_code, "nav_date": trade_time}
        )
        if nav:
            return str(nav.nav)
        show_message("未找到基金净值, 请手动输入", "info")
        # 2. 触发净值更新任务 - 异步更新数据库中的净值
        JobManager().add_task(
            "fund_nav",
            fund_code=fund_code,
            start_date=trade_time,
        )

        return dash.no_update

    except Exception as e:
        logger.error("获取基金净值失败: %s", str(e))
        return dash.no_update
