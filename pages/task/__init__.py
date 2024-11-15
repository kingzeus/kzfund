"""任务管理页面模块

该模块包含任务管理的功能,主要包括:
- 任务的创建和管理
- 任务进度监控
- 任务状态更新
- 任务详情查看

文件结构:
- page.py: 页面主渲染函数
- table.py: 任务列表表格相关
- modal.py: 任务创建弹窗及其回调
- detail_modal.py: 任务详情弹窗相关
- utils.py: 通用工具函数和常量
"""

from .page import render_task_page

__all__ = ["render_task_page"]
