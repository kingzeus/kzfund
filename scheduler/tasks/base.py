from typing import Dict, Any, Tuple
import logging
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseTask(ABC):
    """任务基类"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.progress = 0

    def update_progress(self, progress: int):
        """更新进度"""
        self.progress = progress
        logger.info(f"Task {self.task_id} progress: {progress}%")

    @classmethod
    def validate_params(cls, params: Dict[str, Any]) -> Tuple[bool, str]:
        """验证任务参数

        Args:
            params: 任务参数字典

        Returns:
            (is_valid, error_message): 验证结果元组
            - is_valid: 参数是否有效
            - error_message: 错误信息(验证失败时)
        """
        config = cls.get_config()
        required_params = [
            param for param in config.get("params", []) if param.get("required", False)
        ]

        # 检查必填参数
        for param in required_params:
            if param["key"] not in params:
                return False, f"缺少必填参数: {param['name']}"

            # 检查参数值是否为空
            if not params[param["key"]]:
                return False, f"参数 {param['name']} 不能为空"

        return True, ""

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行任务"""
        pass

    @classmethod
    @abstractmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取任务配置

        Returns:
            包含以下字段的字典:
            - name: 任务名称
            - description: 任务描述
            - timeout: 超时时间(秒)
            - priority: 优先级(1-10)
            - params: 参数配置列表,每个参数包含:
                - name: 参数名称
                - key: 参数键名
                - type: 参数类型(string|number|date|select等)
                - required: 是否必填
                - description: 参数描述
                - default: 默认值
                - options: 选项列表(type为select时使用)
        """
        pass

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        """获取任务类型"""
        pass

    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """获取任务描述"""
        pass
