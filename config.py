"""
应用配置文件
"""

from typing import Dict, Any

# 基本配置
APP_NAME = "基金持仓分析系统"
VERSION = "0.1.0"
DEBUG = True

# 服务器配置
SERVER_CONFIG = {
    "host": "127.0.0.1",
    "port": 8050,
}

# 数据库配置
DATABASE_CONFIG = {
    "path": "fund_analysis.db",
}

# API配置
API_CONFIG = {
    "version": VERSION,
    "title": f"{APP_NAME} API",
    "description": "提供基金持仓分析系统的后端API服务",
    "doc": "/api/doc",
}

# 主题配置
THEME_CONFIG: Dict[str, Any] = {
    "primary_color": "#1890ff",
    "success_color": "#52c41a",
    "warning_color": "#faad14",
    "error_color": "#f5222d",
    "page_padding": 24,
    "card_shadow": "0 2px 8px rgba(0, 0, 0, 0.09)",
}
