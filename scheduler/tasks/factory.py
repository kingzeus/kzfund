from typing import Dict, Type, Any, Tuple
import logging

from config import DEBUG
from .base import BaseTask
from utils.singleton import Singleton


logger = logging.getLogger(__name__)


@Singleton
class TaskFactory:
    """任务工厂(单例模式)"""

    def __init__(self):
        self._tasks: Dict[str, Type[BaseTask]] = {}

    def register(self, task_class: Type[BaseTask]) -> None:
        """注册新的任务类型"""
        task_type = task_class.get_type()
        logger.info(f"注册任务类型: {task_type}")
        self._tasks[task_type] = task_class

        if DEBUG:
            config = task_class.get_config()
            logger.debug(f"任务配置: {task_type}")
            for key, value in config.items():
                logger.debug(f"  {key}: {value}")

    def validate_task_params(
        self, task_type: str, params: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """验证任务参数

        Args:
            task_type: 任务类型
            params: 任务参数

        Returns:
            (is_valid, error_message): 验证结果元组
            - is_valid: 参数是否有效
            - error_message: 错误信息(验证失败时)
        """
        if task_type not in self._tasks:
            logger.error(f"未知的任务类型: {task_type}")
            return False, f"未知的任务类型: {task_type}"

        task_class = self._tasks[task_type]
        return task_class.validate_params(params)

    def create(self, task_type: str, task_id: str) -> BaseTask:
        """创建任务实例"""
        if task_type not in self._tasks:
            error_msg = f"未知的任务类型: {task_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)

        logger.debug(f"创建任务实例: {task_type} (ID: {task_id})")
        return self._tasks[task_type](task_id)

    def execute_task(self, task_type: str, task_id: str, **kwargs) -> Dict[str, Any]:
        """执行任务"""
        logger.info(f"开始执行任务: {task_type} (ID: {task_id})")

        # 先验证参数
        is_valid, error_message = self.validate_task_params(task_type, kwargs)
        if not is_valid:
            logger.error(f"任务参数验证失败: {error_message}")
            raise ValueError(error_message)

        task = self.create(task_type, task_id)
        try:
            result = task.execute(**kwargs)
            logger.info(f"任务执行完成: {task_type} (ID: {task_id})")
            return result
        except Exception as e:
            logger.exception(f"任务执行失败: {task_type} (ID: {task_id})")
            raise

    def get_task_types(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务类型的配置"""
        logger.debug("获取所有任务类型配置")
        return {
            task_type: task_class.get_config()
            for task_type, task_class in self._tasks.items()
        }

    def get_available_tasks(self) -> Dict[str, Type[BaseTask]]:
        """获取所有可用的任务类型"""
        logger.debug("获取所有可用任务类型")
        return self._tasks.copy()
