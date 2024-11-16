"""通用工具函数模块

包含:
- 名称验证函数
- 操作按钮创建函数
"""

from typing import Any, Dict, List, Optional, Tuple

# ============= 常量定义 =============
NAME_MIN_LENGTH = 2  # 名称最小长度
NAME_MAX_LENGTH = 20  # 名称最大长度


# ============= 工具函数 =============
def validate_name(name: Optional[str], field_name: str = "名称") -> Tuple[str, str]:
    """通用的名称验证函数

    Args:
        name: 要验证的名称
        field_name: 字段名称,用于错误提示

    Returns:
        (status, message): 验证状态和提示信息
        - status: "success" 或 "error"
        - message: 错误提示信息
    """
    if not name:
        return "error", f"请输入{field_name}"
    if len(name) < NAME_MIN_LENGTH:
        return "error", f"{field_name}至少需要{NAME_MIN_LENGTH}个字符"
    if len(name) > NAME_MAX_LENGTH:
        return "error", f"{field_name}不能超过{NAME_MAX_LENGTH}个字符"
    return "success", ""


def create_operation_buttons(
    object_id: str,
    action_type: str,
    account_id: Optional[str] = None,
    is_danger: bool = False,
) -> List[Dict[str, Any]]:
    """创建操作按钮配置

    Args:
        object_id: 对象ID
        action_type: 操作类型 ('account' 或 'portfolio')
        account_id: 账户ID(仅用于组合操作)
        is_danger: 是否包含危险操作(删除)按钮

    Returns:
        按钮配置列表,每个按钮包含:
        - icon: 图标名称
        - iconRenderer: 图标渲染器
        - type: 按钮类型
        - custom: 自定义数据
        - danger: 是否为危险按钮(可选)
    """
    buttons = []

    # 编辑按钮
    buttons.append(
        {
            "icon": "antd-edit",
            "iconRenderer": "AntdIcon",
            "type": "link",
            "custom": {
                "id": object_id,
                "action": "edit",
                "type": action_type,
                **({"accountId": account_id} if account_id else {}),
            },
        }
    )

    # 删除按钮
    if is_danger:
        buttons.append(
            {
                "icon": "antd-delete",
                "iconRenderer": "AntdIcon",
                "type": "link",
                "danger": True,
                "custom": {
                    "id": object_id,
                    "action": "delete",
                    "type": action_type,
                    **({"accountId": account_id} if account_id else {}),
                },
            }
        )

    return buttons
