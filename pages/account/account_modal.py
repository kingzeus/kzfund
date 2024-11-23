"""账户编辑弹窗模块

此模块提供账户创建和编辑功能的弹窗组件及相关回调逻辑：
1. 账户编辑弹窗渲染
2. 账户表单验证
3. 账户数据的创建和更新操作

主要组件：
- AccountModal: 账户编辑弹窗
- AccountForm: 账户信息表单
    - 账户名称（必填）
    - 账户描述（可选）
"""

from typing import Any, Dict, List, Optional, Tuple

# Third-party imports
import dash
import feffery_antd_components as fac
from dash import Input, Output, State, callback

# Local imports
from models.account import update_account
from pages.account.table import get_account_table_data
from pages.account.utils import validate_name

# UI Constants
MODAL_WIDTH = 500  # 弹窗宽度(像素)
FORM_LABEL_SPAN = 6  # 表单标签列宽度(antd栅格系统, 总24列)
FORM_WRAPPER_SPAN = 18  # 表单内容列宽度(antd栅格系统, 总24列)
TEXT_AREA_MIN_ROWS = 3  # 文本域最小行数
TEXT_AREA_MAX_ROWS = 5  # 文本域最大行数(超出显示滚动条)


def render_account_modal() -> fac.AntdModal:
    """渲染账户编辑弹窗组件

    Returns:
        fac.AntdModal: 包含以下内容的弹窗组件：
            - 标题：新建账户
            - 表单：
                - 账户名称输入框（必填，带验证）
                - 账户描述文本框（可选，支持多行）
            - 操作按钮：
                - 确定：提交表单
                - 取消：关闭弹窗
    """
    return fac.AntdModal(
        id="account-modal",
        title="新建账户",
        visible=False,
        maskClosable=False,
        width=MODAL_WIDTH,
        renderFooter=True,
        okText="确定",
        cancelText="取消",
        children=[_render_account_form()],
    )


def _render_account_form() -> fac.AntdForm:
    """渲染账户信息表单

    Returns:
        fac.AntdForm: 包含账户信息字段的表单组件
    """
    return fac.AntdForm(
        id="account-form",
        labelCol={"span": FORM_LABEL_SPAN},
        wrapperCol={"span": FORM_WRAPPER_SPAN},
        children=[
            # 账户名称输入框
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
            # 账户描述输入框
            fac.AntdFormItem(
                fac.AntdInput(
                    id="account-desc-input",
                    mode="text-area",
                    placeholder="请输入账户描述",
                    allowClear=True,
                    autoSize={"minRows": TEXT_AREA_MIN_ROWS, "maxRows": TEXT_AREA_MAX_ROWS},
                ),
                label="账户描述",
                id="account-desc-form-item",
            ),
        ],
    )


# 账户弹窗回调函数
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
    """显示新建账户对话框回调

    当点击新建账户按钮时，显示账户编辑弹窗并清空表单

    Args:
        n_clicks: 按钮点击次数

    Returns:
        Tuple[bool, str, str, str]:
            - 弹窗显示状态
            - 账户名称输入框值
            - 账户描述输入框值
            - 编辑账户ID
    """
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
    """账户名称验证回调

    实时验证输入的账户名称是否符合要求

    Args:
        name: 输入的账户名称

    Returns:
        Tuple[str, str]:
            - 验证状态：'success' | 'error'
            - 帮助文本：验证通过为空，验证失败显示错误信息
    """
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
    """处理账户创建或编辑回调

    当点击弹窗确定按钮时，根据是否有editing_id判断是创建还是编辑操作

    Args:
        ok_counts: 确定按钮点击次数
        name: 账户名称
        description: 账户描述
        validate_status: 名称验证状态
        editing_id: 正在编辑的账户ID，为空表示新建

    Returns:
        Tuple[List[Dict[str, Any]], bool, str, str]:
            - 更新后的账户列表数据
            - 弹窗显示状态
            - 账户名称输入框值
            - 账户描述输入框值
    """
    if ok_counts and name and validate_status == "success":

        update_account(
            editing_id,
            {"name": name, "description": description},
        )

        return get_account_table_data(), False, "", ""
    return get_account_table_data(), dash.no_update, dash.no_update, dash.no_update
