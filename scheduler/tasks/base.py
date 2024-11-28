import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Protocol, Tuple

logger = logging.getLogger(__name__)

# ------------常用参数定义------------
# 基金代码参数
PARAM_FUND_CODE = {
    "name": "基金代码",
    "key": "fund_code",
    "type": "fund-code-aio",
    "required": True,
    "description": "要更新的基金代码",
}
# 子任务间隔参数
PARAM_SUB_TASK_DELAY = {
    "name": "子任务间隔",
    "key": "sub_task_delay",
    "type": "number",
    "required": False,
    "default": 2,
    "description": "子任务间隔时间，随机增加间隔上限",
}

# 子任务间隔参数
PARAM_PAGE = {
    "name": "页码",
    "key": "page",
    "type": "number",
    "required": True,
    "default": 1,
    "description": "页码",
}
PARAM_PAGE_SIZE = {
    "name": "每页数据量",
    "key": "page_size",
    "type": "number",
    "required": False,
    "default": 100,
    "description": "每页数据量",
}


# 基金类型选择参数


# 基金类型枚举
class FundType:
    """基金类型枚举"""

    STOCK = 1  # 股票型
    MIXED = 2  # 混合型
    INDEX = 3  # 指数型
    QDII = 4  # QDII
    LOF = 5  # LOF
    BOND = 6  # 债券型
    FOF = 7  # FOF
    ALL = 10  # 全部数据


# 基金类型参数配置
PARAM_FUND_TYPE = {
    "name": "类型",
    "key": "fund_type",
    "type": "select",
    "required": True,
    "description": "选择要同步的数据类型",
    "default": FundType.ALL,
    "select_options": [
        {"label": "全部数据", "value": FundType.ALL},
        {"label": "股票型", "value": FundType.STOCK},
        {"label": "混合型", "value": FundType.MIXED},
        {"label": "指数型", "value": FundType.INDEX},
        {"label": "QDII", "value": FundType.QDII},
        {"label": "LOF", "value": FundType.LOF},
        {"label": "债券型", "value": FundType.BOND},
        {"label": "FOF", "value": FundType.FOF},
    ],
}


class TaskProgressUpdater(Protocol):
    """任务进度更新器协议"""

    def update_task_progress(self, task_id: str, progress: int) -> None:
        """更新任务进度"""


class BaseTask(ABC):
    """任务基类"""

    def __init__(self, task_id: str, progress_updater: Optional[TaskProgressUpdater] = None):
        self.task_id = task_id
        self.progress = 0
        self._progress_updater = progress_updater

    def update_progress(self, progress: int):
        """更新进度

        Args:
            progress: 进度值(0-100)
        """
        self.progress = progress
        # 更新进度缓存
        if self._progress_updater:
            self._progress_updater.update_task_progress(self.task_id, progress)
        logger.info("Task %s progress: %d%%", self.task_id, progress)

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

    @classmethod
    @abstractmethod
    def get_config(cls) -> Dict[str, Any]:
        """获取任务配置

        Returns:
            包含以下字段的字典:
            - name: 任务名称
            - description: 任务描述
            - timeout: 超时时间(秒)
            - params: 参数配置列表,每个参数包含:
                - name: 参数名称
                - key: 参数键名
                - type: 参数类型(string|number|date|select等)
                - required: 是否必填
                - description: 参数描述
                - default: 默认值
                - select_options: 选项列表(type为select时使用)
        """

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        """获取任务类型"""

    @classmethod
    @abstractmethod
    def get_description(cls) -> str:
        """获取任务描述"""
