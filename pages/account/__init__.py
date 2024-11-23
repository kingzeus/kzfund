"""账户管理页面模块

该模块包含账户和投资组合的管理功能,主要包括:
- 账户的增删改查
- 投资组合的增删改查
- 嵌套表格展示账户和组合的层级关系

文件结构:
- task_page.py: 页面主渲染函数
- table.py: 账户表格相关组件和回调
- account_modal.py: 账户编辑弹窗相关
- portfolio_modal.py: 组合编辑弹窗相关
- delete_modal.py: 删除确认弹窗相关
- utils.py: 通用工具函数
"""

from pages.account.page import render_account_page

__all__ = ["render_account_page"]
