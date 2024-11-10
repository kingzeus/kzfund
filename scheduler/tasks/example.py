import time
from datetime import datetime
from typing import Dict, Any
import logging
from .base import BaseTask

logger = logging.getLogger(__name__)


class ExampleTask(BaseTask):
    """示例任务"""

    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        return {
            "name": "示例任务",
            "description": "这是一个示例任务",
            "timeout": 1800,
            "priority": 1,
        }

    @classmethod
    def get_type(cls) -> str:
        return "example_task"

    def execute(self, **kwargs) -> Dict[str, Any]:
        logger.info(f"[{datetime.now()}] 开始执行任务 {self.task_id}")

        # 模拟耗时操作
        for i in range(5):
            time.sleep(1)
            progress = (i + 1) * 20
            self.update_progress(progress)

        return {
            "message": "Task completed successfully",
            "task_id": self.task_id,
            "custom_param": kwargs.get("custom_param"),
        }
