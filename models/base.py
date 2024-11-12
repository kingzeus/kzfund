from peewee import Model, SqliteDatabase, DateTimeField
from datetime import datetime
import logging
from config import DATABASE_CONFIG
from contextlib import contextmanager
from utils.singleton import Singleton


logger = logging.getLogger(__name__)


@Singleton
class Database:
    def __init__(self):
        # 初始化属性
        self.db = None
        self.db_path = None

    def connect(self):
        if self.db.is_closed():
            self.db.connect()

    def open(self, db_path: str):
        new_db_path = db_path or DATABASE_CONFIG["path"]
        if self.db is not None:
            if new_db_path == self.db_path:
                return
            else:
                self.close()

        self.db_path = new_db_path
        self.db = SqliteDatabase(self.db_path)
        logger.debug(f"初始化数据库连接: {self.db_path}")

    def close(self):
        if self.db is not None:
            if not self.db.is_closed():
                logger.debug("关闭数据库连接")
                self.db.close()
                self.db_path = None
                self.db = None

    def get_db(self):
        if self.db is None:
            error_msg = "数据库未初始化"
            logger.error(error_msg)
            raise Exception(error_msg)
        return self.db


def init_db(db_path: str = None):
    """初始化数据库连接"""
    try:
        Database().open(db_path)
        BaseModel._meta.database = Database().get_db()
        logger.info(f"数据库初始化成功: {db_path or DATABASE_CONFIG['path']}")
        return Database().get_db()
    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}", exc_info=True)
        raise


class BaseModel(Model):
    """基础模型类"""

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = None  # 将在初始化时设置

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


@contextmanager
def db_connection(db_path: str = None):
    """数据库连接上下文管理器"""
    try:
        Database().open(db_path)
        Database().connect()
        logger.debug("打开数据库连接")
        yield Database().get_db()
    except Exception as e:
        logger.error(f"数据库操作失败: {str(e)}", exc_info=True)
        raise
    finally:
        Database().close()
        logger.debug("关闭数据库连接")


# 初始化默认数据库连接
init_db()
