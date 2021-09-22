import datetime

from peewee import TextField, DateTimeField, BooleanField, ForeignKeyField, IntegerField
from playhouse.postgres_ext import ArrayField

from .people import BaseModel


class TaskCode(BaseModel):
    not_checked_humans_ids = ArrayField(IntegerField)
    task_code = TextField()
    created_at = DateTimeField(default=datetime.datetime.now)
    is_executed = BooleanField(default=False)
    executed_at = DateTimeField(null=True)
