from typing import Optional, Tuple

import feffery_antd_components as fac
from dash import Input, Output, State, callback, dcc
from dash.exceptions import PreventUpdate

from models.database import add_portfolio, update_portfolio
from pages.account.table import get_account_table_data
from pages.account.utils import validate_name

"""组合编辑弹窗模块

提供投资组合的创建和编辑功能:
- 渲染组合编辑弹窗
- 处理组合名称验证
- 处理组合创建和编辑操作
"""


def render_portfolio_modal() -> fac.AntdModal:
    """渲染组合编辑弹窗

    Returns:
        AntdModal: 包含组合表单的弹窗组件
        - 所属账户选择器(新建时显示)
        - 组合名称输入框(必填)
        - 组合描述输入框(可选)
    """
    return fac.AntdModal(
        id="portfolio-modal",
        title="新建组合",
        visible=False,
        renderFooter=True,
        maskClosable=False,
        width=500,
        okText="确定",
        cancelText="取消",
        children=[
            dcc.Store(id="portfolio-edit-mode", data=False),
            fac.AntdForm(
                labelCol={"span": 6},
                wrapperCol={"span": 18},
                children=[
                    fac.AntdFormItem(
                        fac.AntdSelect(
                            id="portfolio-account-select",
                            placeholder="请选择账户",
                            options=[],
                            style={"width": "100%"},
                        ),
                        label="所属账户",
                        required=True,
                        id="portfolio-account-form-item",
                        style={"display": "none"},
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="portfolio-name-input",
                            placeholder="请输入组合名称",
                            allowClear=True,
                        ),
                        label="组合名称",
                        required=True,
                        id="portfolio-name-form-item",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="portfolio-desc-input",
                            mode="text-area",
                            placeholder="请输入组合描述",
                            allowClear=True,
                            autoSize={"minRows": 3, "maxRows": 5},
                        ),
                        label="组合描述",
                        id="portfolio-desc-form-item",
                    ),
                ],
            ),
        ],
    )


@callback(
    [
        Output("portfolio-modal", "visible"),
        Output("portfolio-account-select", "options"),
        Output("portfolio-account-form-item", "style"),
        Output("portfolio-edit-mode", "data"),
    ],
    Input("add-portfolio-btn", "nClicks"),
    State("account-store", "data"),
    prevent_initial_call=True,
)
def show_portfolio_modal(n_clicks, accounts_data):
    """显示新建组合对话框"""
    if not n_clicks:
        raise PreventUpdate

    account_options = [
        {
            "label": account["name"],
            "value": account["id"],
        }
        for account in accounts_data
    ]

    return True, account_options, {"display": "block"}, False


@callback(
    [
        Output("portfolio-name-form-item", "validateStatus"),
        Output("portfolio-name-form-item", "help"),
    ],
    Input("portfolio-name-input", "value"),
    prevent_initial_call=True,
)
def validate_portfolio_name(name: Optional[str]) -> Tuple[str, str]:
    """验证组合名称"""
    return validate_name(name, "组合名称")


@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("portfolio-modal", "visible", allow_duplicate=True),
        Output("portfolio-account-select", "value", allow_duplicate=True),
        Output("portfolio-name-input", "value", allow_duplicate=True),
        Output("portfolio-desc-input", "value", allow_duplicate=True),
    ],
    Input("portfolio-modal", "okCounts"),
    [
        State("portfolio-edit-mode", "data"),
        State("portfolio-account-select", "value"),
        State("portfolio-name-input", "value"),
        State("portfolio-desc-input", "value"),
        State("editing-account-id", "data"),
    ],
    prevent_initial_call=True,
)
def handle_portfolio_create_or_edit(
    ok_counts, is_edit_mode, account_id, name, description, editing_id
):
    """处理组合创建或编辑"""
    if not ok_counts or not name:
        raise PreventUpdate

    if is_edit_mode and editing_id:
        update_portfolio(
            editing_id,
            {
                "name": name,
                "description": description,
            },
        )
    else:
        if not account_id:
            raise PreventUpdate
        add_portfolio(
            account_id=account_id,
            name=name,
            description=description,
            is_default=False,
        )

    return get_account_table_data(), False, None, "", ""
