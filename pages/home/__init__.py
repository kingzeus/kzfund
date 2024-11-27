"""首页仪表盘模块

该模块包含首页仪表盘的展示功能,主要包括:
- 数据概览卡片
- 资产配置图表
- 收益走势图表

文件结构:
- task_page.py: 页面主渲染函数
- home_overview.py: 数据概览卡片相关
- charts.py: 图表相关组件
- utils.py: 通用工具函数
"""

from .home_page import render_home_page

__all__ = ["render_home_page"]
