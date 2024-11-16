"""
应用配置文件
"""

import os
from typing import Any, Dict

# 基本配置
APP_NAME = "基金持仓分析系统"  # 应用名称
VERSION = "0.1.0"  # 应用版本号
DEBUG = True  # 调试模式开关

# 获取项目根目录
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# 日志配置
LOG_CONFIG = {
    "version": 1,  # dictConfig版本号，固定为1
    "disable_existing_loggers": False,  # 是否禁用现有的日志记录器
    # 日志格式定义
    "formatters": {
        # 默认格式：简单格式，用于控制台输出
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        # 详细格式：包含更多信息，用于文件日志
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    # 日志处理器配置
    "handlers": {
        # 控制台处理器
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        },
        # 常规日志文件处理器
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": os.path.join(ROOT_DIR, "logs", "app.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,  # 保留5个备份文件
            "encoding": "utf-8",
            "level": "DEBUG" if DEBUG else "INFO",
        },
        # 错误日志文件处理器
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "detailed",
            "filename": os.path.join(ROOT_DIR, "logs", "error.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "encoding": "utf-8",
            "level": "ERROR",
        },
    },
    # 根日志记录器配置
    "root": {
        "level": "DEBUG" if DEBUG else "INFO",
        "handlers": ["console", "file", "error_file"],
    },
    # 特定模块的日志记录器配置
    "loggers": {
        # Flask开发服务器的日志配置
        "werkzeug": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["console", "file"],
            "propagate": False,  # 不传播到父级记录器
        },
        # 调度器模块的日志配置
        "scheduler": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        # 数据源模块的日志配置
        "data_source": {
            "level": "DEBUG" if DEBUG else "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

# 服务器配置
SERVER_CONFIG = {
    "host": "127.0.0.1",  # 服务器监听地址
    "port": 8050,  # 服务器监听端口
}

# 数据库配置
DATABASE_CONFIG = {
    "path": os.path.join(ROOT_DIR, "database", "fund_analysis.v4.db")  # SQLite数据库文件路径
}

# API配置
API_CONFIG = {
    "version": VERSION,  # API版本号
    "title": f"{APP_NAME} API",  # API文档标题
    "description": "提供基金持仓分析系统的后端API服务",  # API文档描述
    "doc": "/api/doc",  # API文档路径
}

# 主题配置
THEME_CONFIG: Dict[str, Any] = {
    "primary_color": "#1890ff",  # 主色调
    "success_color": "#52c41a",  # 成功状态颜色
    "warning_color": "#faad14",  # 警告状态颜色
    "error_color": "#f5222d",  # 错误状态颜色
    "page_padding": 24,  # 页面内边距
    "card_shadow": "0 2px 8px rgba(0, 0, 0, 0.09)",  # 卡片阴影效果
}

# 数据源配置
DATA_SOURCE_DEFAULT = "eastmoney"  # 默认数据源（东方财富）

# 任务调度器配置
SCHEDULER_CONFIG = {
    # Flask-APScheduler 配置
    "SCHEDULER_API_ENABLED": True,  # 启用调度器API
    "SCHEDULER_API_PREFIX": "/scheduler",  # API前缀
    "SCHEDULER_TIMEZONE": "Asia/Shanghai",  # 时区设置
    # 任务存储配置
    "SCHEDULER_JOB_DEFAULTS": {
        "coalesce": False,  # 是否合并延迟的任务
        "max_instances": 1,  # 同一个任务的最大实例数
        "misfire_grace_time": 60,  # 任务错过执行时间的容错时间（秒）
    },
    # 自定义配置
    "DEFAULT_TIMEOUT": 3600,  # 默认任务超时时间（秒）
}
