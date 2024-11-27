import logging
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Optional

from peewee import DatabaseError, DateTimeField, Model, SqliteDatabase

from config import DATABASE_CONFIG
from utils.singleton import Singleton

logger = logging.getLogger(__name__)


@Singleton
class Database:
    def __init__(self):
        # 初始化属性
        self.databases: Dict[str, Optional[SqliteDatabase]] = {
            "main": None,  # 主数据库(账户、组合等基础数据)
            "task": None,  # 任务数据库
        }
        self.db_paths: Dict[str, Optional[str]] = {
            "main": None,
            "task": None,
        }

    def connect(self, db_name: str = "main"):
        if self.databases[db_name] and self.databases[db_name].is_closed():
            self.databases[db_name].connect()

    def open(self, db_path: str, db_name: str = "main"):
        new_db_path = db_path or DATABASE_CONFIG["paths"][db_name]
        if self.databases[db_name] is not None and new_db_path == self.db_paths[db_name]:
            return

        if self.databases[db_name] is not None:
            self.close(db_name)

        self.db_paths[db_name] = new_db_path
        self.databases[db_name] = SqliteDatabase(self.db_paths[db_name])
        logger.debug("初始化数据库连接[%s]: %s", db_name, self.db_paths[db_name])

    def close(self, db_name: str = "main"):
        if self.databases[db_name] is not None:
            if not self.databases[db_name].is_closed():
                logger.debug("关闭数据库连接[%s]", db_name)
                self.databases[db_name].close()
                self.db_paths[db_name] = None
                self.databases[db_name] = None

    def get_db(self, db_name: str = "main"):
        if self.databases[db_name] is None:
            error_msg = f"数据库[{db_name}]未初始化"
            logger.error(error_msg)
            raise DatabaseError(error_msg)
        return self.databases[db_name]


class BaseModel(Model):
    """基础模型类"""

    created_at = DateTimeField(default=datetime.now)  # 创建时间
    updated_at = DateTimeField(default=datetime.now)  # 更新时间

    class Meta:
        database = None  # 将在初始化时设置
        db_name = "main"  # 默认使用主数据库

    @classmethod
    def get_database(cls):
        """获取模型对应的数据库连接"""
        db = Database().get_db(cls._meta.db_name)
        if cls._meta.database is None:
            cls._meta.database = db
        return db

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)

    def to_dict(self) -> dict:
        """将模型实例转换为可JSON序列化的字典

        Returns:
            包含模型基本属性的字典
        """
        return {
            "created_at": (
                self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None
            ),
            "updated_at": (
                self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None
            ),
        }


@contextmanager
def db_connection(db_path: str = None, db_name: str = "main"):
    """数据库连接上下文管理器"""
    try:
        Database().open(db_path, db_name)
        Database().connect(db_name)
        logger.debug("打开数据库连接[%s]", db_name)
        yield Database().get_db(db_name)
    except Exception as e:
        logger.error("数据库操作失败[%s]: %s", db_name, str(e), exc_info=True)
        raise
    finally:
        Database().close(db_name)
        logger.debug("关闭数据库连接[%s]", db_name)


def init_db(db_paths: Dict[str, str] = None):
    """初始化数据库连接"""
    try:
        paths = db_paths or DATABASE_CONFIG["paths"]
        for db_name, path in paths.items():
            Database().open(path, db_name)
            logger.info("数据库[%s]初始化成功: %s", db_name, path)
        return Database()
    except Exception as e:
        logger.error("数据库初始化失败: %s", str(e), exc_info=True)
        raise


# 初始化默认数据库连接
init_db()
