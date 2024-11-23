from datetime import datetime
from typing import Any, Dict, Optional

from flask_apscheduler import APScheduler

from scheduler.tasks import TaskStatus

scheduler = APScheduler()


class TaskResult:
    def __init__(self):
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.result = None
        self.error = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
        }


task_results = {}
