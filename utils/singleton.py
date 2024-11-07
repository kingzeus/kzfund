from typing import Dict, Any, Type, TypeVar

T = TypeVar("T")


class Singleton:
    """单例模式装饰器"""

    _instances: Dict[Type, Any] = {}

    def __init__(self, cls: Type[T]):
        self._cls = cls

    def __call__(self, *args, **kwargs) -> T:
        # 添加双重检查锁定模式
        if self._cls not in self._instances:
            # 如果实例不存在,加锁创建
            with self._get_lock():
                if self._cls not in self._instances:
                    self._instances[self._cls] = self._cls(*args, **kwargs)
        return self._instances[self._cls]

    def _get_lock(self):
        """获取锁对象"""
        # 使用类属性作为锁
        if not hasattr(self._cls, "_lock"):
            from threading import Lock

            setattr(self._cls, "_lock", Lock())
        return getattr(self._cls, "_lock")

    def __getattr__(self, name):
        return getattr(self._cls, name)
