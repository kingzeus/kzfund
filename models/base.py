from peewee import Model, SqliteDatabase, DateTimeField
from datetime import datetime
from config import DATABASE_CONFIG
from contextlib import contextmanager
from utils.singleton import Singleton


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
        self.close()
        self.db_path = db_path or DATABASE_CONFIG["path"]
        self.db = SqliteDatabase(self.db_path)
        print(f"初始化数据库连接: {self.db_path}")

    def close(self):
        if self.db is not None:
            if not self.db.is_closed():
                self.db.close()
                self.db_path = None
                self.db = None

    def get_db(self):
        if self.db is None:
            raise Exception("数据库未初始化")
        return self.db


def init_db(db_path: str = None):
    """初始化数据库连接"""
    Database().open(db_path)
    BaseModel._meta.database = Database().get_db()
    return Database().get_db()


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
    db_instance = Database(db_path)
    db_instance.connect()
    try:
        yield db_instance.get_db()
    finally:
        db_instance.close()


# 初始化默认数据库连接
init_db()
