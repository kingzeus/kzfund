from peewee import Model, SqliteDatabase, DateTimeField
from datetime import datetime
from config import DATABASE_CONFIG
from contextlib import contextmanager

# 数据库实例
db = SqliteDatabase(DATABASE_CONFIG["path"])


class BaseModel(Model):
    """基础模型类"""

    created_at = DateTimeField(default=datetime.now)
    updated_at = DateTimeField(default=datetime.now)

    class Meta:
        database = db

    def save(self, *args, **kwargs):
        self.updated_at = datetime.now()
        return super().save(*args, **kwargs)


@contextmanager
def db_connection():
    """数据库连接上下文管理器"""
    db.connect(reuse_if_open=True)
    try:
        yield db
    finally:
        if not db.is_closed():
            db.close()
