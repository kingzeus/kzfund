"""通用工具函数模块

包含:
- 操作按钮创建函数
- 账户-组合级联选择器选项构建
"""

from typing import Any, Dict, List

from models.account import ModelAccount
from models.database import get_record_list


def create_operation_buttons(transaction_id: str) -> List[Dict[str, Any]]:
    """创建操作按钮配置

    Args:
        transaction_id: 交易记录ID

    Returns:
        按钮配置列表,每个按钮包含:
        - icon: 图标名称
        - iconRenderer: 图标渲染器
        - type: 按钮类型
        - custom: 自定义数据
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


def build_cascader_options() -> List[Dict[str, Any]]:
    """构建账户-组合级联选择器选项

    Returns:
        级联选择器选项列表,每个选项包含:
        - label: 显示名称
        - value: 选项值
        - children: 子选项列表(组合)
    """
    accounts = get_record_list(ModelAccount)
    cascader_options = []

    for account in accounts:
        portfolios = account.portfolios
        portfolio_children = [
            {
                "label": p.name,
                "value": p.id,
            }
            for p in portfolios
        ]
        cascader_options.append(
            {
                "label": account.name,
                "value": account.id,
                "children": portfolio_children,
            }
        )

    return cascader_options
