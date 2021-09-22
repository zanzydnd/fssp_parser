import datetime

from peewee import TextField, DateTimeField, BooleanField, ForeignKeyField

from .people import BaseModel, NotCheckedHuman


class TaskCode(BaseModel):
    human = ForeignKeyField(NotCheckedHuman, related_name="task_codes")
    task_code = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    is_executed = BooleanField(default=False)
    executed_at = DateTimeField(null=True)
