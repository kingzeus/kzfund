from typing import Tuple, Optional, List, Dict, Any
import dash
from dash import Input, Output, State, callback
import feffery_antd_components as fac

from models.database import add_account, update_account
from .table import get_account_table_data
from .utils import validate_name


"""账户编辑弹窗模块

提供账户创建和编辑功能的弹窗组件及相关回调:
- 渲染账户编辑弹窗
- 处理账户名称验证
- 处理账户创建和编辑操作
"""


def render_account_modal() -> fac.AntdModal:
    """渲染账户编辑弹窗

    Returns:
        AntdModal: 包含账户表单的弹窗组件
        - 账户名称输入框(必填)
        - 账户描述输入框(可选)
    """
    return fac.AntdModal(
        id="account-modal",
        title="新建账户",
        visible=False,
        maskClosable=False,
        width=500,
        renderFooter=True,
        okText="确定",
        cancelText="取消",
        children=[
            fac.AntdForm(
                id="account-form",
                labelCol={"span": 6},
                wrapperCol={"span": 18},
                children=[
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="account-name-input",
                            placeholder="请输入账户名称",
                            allowClear=True,
                        ),
                        label="账户名称",
                        required=True,
                        id="account-name-form-item",
                        validateStatus="validating",
                        help="",
                    ),
                    fac.AntdFormItem(
                        fac.AntdInput(
                            id="account-desc-input",
                            mode="text-area",
                            placeholder="请输入账户描述",
                            allowClear=True,
                            autoSize={"minRows": 3, "maxRows": 5},
                        ),
                        label="账户描述",
                        id="account-desc-form-item",
                    ),
                ],
            )
        ],
    )


# 账户相关回调
@callback(
    [
        Output("account-modal", "visible", allow_duplicate=True),
        Output("account-name-input", "value", allow_duplicate=True),
        Output("account-desc-input", "value", allow_duplicate=True),
        Output("editing-account-id", "data", allow_duplicate=True),
    ],
    Input("add-account-btn", "nClicks"),
    prevent_initial_call=True,
)
def show_account_modal(n_clicks: Optional[int]) -> Tuple[bool, str, str, str]:
    """显示新建账户对话框"""
    if n_clicks:
        return True, "", "", ""
    return dash.no_update


@callback(
    [
        Output("account-name-form-item", "validateStatus"),
        Output("account-name-form-item", "help"),
    ],
    Input("account-name-input", "value"),
    prevent_initial_call=True,
)
def validate_account_name(name: Optional[str]) -> Tuple[str, str]:
    """验证账户名称"""
    return validate_name(name, "账户名称")


@callback(
    [
        Output("account-store", "data", allow_duplicate=True),
        Output("account-modal", "visible", allow_duplicate=True),
        Output("account-name-input", "value", allow_duplicate=True),
        Output("account-desc-input", "value", allow_duplicate=True),
    ],
    [Input("account-modal", "okCounts")],
    [
        State("account-name-input", "value"),
        State("account-desc-input", "value"),
        State("account-name-form-item", "validateStatus"),
        State("editing-account-id", "data"),
    ],
    prevent_initial_call=True,
)
def handle_account_create_or_edit(
    ok_counts: Optional[int],
    name: Optional[str],
    description: Optional[str],
    validate_status: str,
    editing_id: str,
) -> Tuple[List[Dict[str, Any]], bool, str, str]:
    """处理账户创建编辑"""
    if ok_counts and name and validate_status == "success":
        if editing_id:
            update_account(editing_id, name, description)
        else:
            add_account(name, description)
        return get_account_table_data(), False, "", ""
    return get_account_table_data(), dash.no_update, dash.no_update, dash.no_update
