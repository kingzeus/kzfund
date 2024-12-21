from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField, TextField

from kz_dash.models.base import BaseModel


class ModelTask(BaseModel):
    task_id = CharField(max_length=36, primary_key=True)
    parent_task = ForeignKeyField("self", backref="sub_tasks", null=True)  # 父任务
    name = CharField(max_length=100)
    type = CharField(max_length=50)  # 任务类型
    delay = IntegerField(default=0)  # 延迟时间（秒）
    status = CharField(max_length=20)
    progress = IntegerField(default=0)
    input_params = TextField(null=True)  # 输入参数
    result = TextField(null=True)
    error = TextField(null=True)
    start_time = DateTimeField(null=True)  # 任务开始执行的时间
    end_time = DateTimeField(null=True)  # 结束时间
    timeout = IntegerField(default=3600)  # 超时时间（秒）

    class Meta:
        table_name = "task"
        db_name = "task"

    def to_dict(self) -> dict:
        """将任务实例转换为可JSON序列化的字典

        Returns:
            包含任务基本属性的字典
        """
        # 获取基类的字典
        result = super().to_dict()
        # 添加任务特有的字段
        result.update(
            {
                "task_id": self.task_id,
                "parent_task_id": self.parent_task_id,
                "name": self.name,
                "type": self.type,
                "status": self.status,
                "progress": self.progress,
                "delay": self.delay,
                "timeout": self.timeout,
                "start_time": (
                    self.start_time.strftime("%Y-%m-%d %H:%M:%S") if self.start_time else None
                ),
                "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S") if self.end_time else None,
                "input_params": self.input_params,
                "result": self.result,
                "error": self.error,
            }
        )
        return result
