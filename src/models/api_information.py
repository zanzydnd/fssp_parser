import datetime

from peewee import TextField, DateTimeField, BooleanField, ForeignKeyField, IntegerField

from .people import BaseModel, NotCheckedHuman


class TaskCode(BaseModel):
    human = ForeignKeyField(NotCheckedHuman, related_name="task_codes")
    task_code = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    is_executed = BooleanField(default=False)
    executed_at = DateTimeField(null=True)


class Statistic(BaseModel):
    num_of_new_records = IntegerField()
    task = ForeignKeyField(TaskCode, related_name="statistics")
    data = DateTimeField(default=datetime.datetime.now)
