import datetime

from peewee import TextField, DateTimeField, BooleanField

from src.models.people import BaseModel


class TaskCode(BaseModel):
    task_code = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    is_executed = BooleanField(default=False)
    executed_at = DateTimeField(default=datetime.datetime.now)
