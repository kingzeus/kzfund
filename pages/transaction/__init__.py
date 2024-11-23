"""交易记录管理页面模块

该模块包含交易记录的管理功能,主要包括:
- 交易记录的增删改查
- 支持手工录入交易记录
- 表格展示所有交易记录

文件结构:
- task_page.py: 页面主渲染函数
- table.py: 交易记录表格相关组件和回调
- modal.py: 交易记录编辑弹窗及其回调
- delete_modal.py: 删除确认弹窗相关
- utils.py: 通用工具函数
"""

from .page import render_transaction_page

__all__ = ["render_transaction_page"]
