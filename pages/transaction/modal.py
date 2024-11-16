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
from models.database import add_transaction, get_transactions, update_transaction

from .utils import build_cascader_options

# ============= 日志配置 =============
logger = logging.getLogger(__name__)

# ============= 常量定义 =============
TRANSACTION_TYPES = [
    {"label": "买入", "value": "buy"},
    {"label": "卖出", "value": "sell"},
]

FORM_LAYOUT = {"labelCol": {"span": 6}, "wrapperCol": {"span": 18}}


# ============= 组件渲染函数 =============
def render_transaction_modal() -> fac.AntdModal:
    """渲染交易记录编辑弹窗

    Returns:
        AntdModal: 包含以下表单项的弹窗组件:
        - 投资组合选择器(级联选择)
        - 基金代码输入(自动完成)
        - 交易类型选择
        - 交易金额输入
        - 交易时间选择
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
                    # 投资组合选择
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
                    # 基金代码输入
                    fac.AntdFormItem(
                        FundCodeAIO(aio_id="fund-code-aio"),
                        label="基金代码",
                        required=True,
                    ),
                    # 交易类型选择
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
                    # 交易金额输入
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
                    # 交易时间选择
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
        Output("trade-time-picker", "value", allow_duplicate=True),
        Output("editing-transaction-id", "data", allow_duplicate=True),
    ],
    Input("add-transaction-btn", "nClicks"),
    prevent_initial_call=True,
)
def show_transaction_modal(n_clicks: Optional[int]) -> Tuple:
    """显示新建交易对话框

    Args:
        n_clicks: 按钮点击次数

    Returns:
        tuple: 包含所有表单项的初始值
    """
    if not n_clicks:
        raise PreventUpdate

    cascader_options = build_cascader_options()
    return (
        True,  # modal visible
        "新建交易",  # modal title
        cascader_options,  # cascader options
        None,  # cascader value
        "",  # fund code
        None,  # transaction type
        None,  # amount
        None,  # trade time
        "",  # editing id
    )


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
    trade_time: Optional[str],
    editing_id: Optional[str],
) -> Tuple[List[Dict[str, Any]], bool]:
    """处理交易记录保存

    Args:
        ok_counts: 确认按钮点击次数
        portfolio_path: 组合选择路径
        fund_code: 基金代码
        transaction_type: 交易类型
        amount: 交易金额
        trade_time: 交易时间
        editing_id: 正在编辑的交易ID

    Returns:
        tuple: (更新后的数据, 弹窗可见性)
    """
    # 验证必填字段
    if not ok_counts or not all([portfolio_path, fund_code, transaction_type, amount, trade_time]):
        raise PreventUpdate

    try:
        # 获取组合ID
        portfolio_id = portfolio_path[-1] if portfolio_path else None
        if not portfolio_id:
            raise PreventUpdate

        # 处理日期时间
        if isinstance(trade_time, str) and len(trade_time) == 10:
            trade_date = datetime.strptime(trade_time, "%Y-%m-%d")
            trade_datetime = datetime.combine(trade_date, datetime.min.time())
        else:
            trade_datetime = datetime.strptime(trade_time, "%Y-%m-%d %H:%M:%S")

        # 保存交易记录
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
            return get_transactions(), False
        logger.error("保存交易记录失败")

    except Exception as e:
        logger.error(f"处理交易保存失败: {str(e)}", exc_info=True)

    return dash.no_update, dash.no_update
