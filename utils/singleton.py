from typing import Dict, Any, Type, TypeVar

T = TypeVar("T")


class Singleton:
    """单例模式装饰器"""

    _instances: Dict[Type, Any] = {}

    def __init__(self, cls: Type[T]):
        self._cls = cls

    def __call__(self, *args, **kwargs) -> T:
        if self._cls not in self._instances:
            self._instances[self._cls] = self._cls(*args, **kwargs)
        return self._instances[self._cls]

    def __getattr__(self, name):
        return getattr(self._cls, name)
