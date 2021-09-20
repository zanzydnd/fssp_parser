import datetime

from peewee import Model, CharField, BooleanField, ForeignKeyField, DateTimeField, IntegerField, TextField, \
    BigIntegerField

postgre_db = None


class BaseModel(Model):
    class Meta:
        pass


class NotCheckedHuman(BaseModel):
    name = CharField(max_length=100, null=False)
    lastname = CharField(max_length=100, null=False)
    secondname = CharField(max_length=100, null=True)
    region = IntegerField()
    is_checked = BooleanField(default=False, null=False)


class FSSPHuman(BaseModel):
    whom_from = ForeignKeyField(NotCheckedHuman, backref="fssp_humans")
    name = CharField(max_length=100, null=False)
    lastname = CharField(max_length=100, null=False)
    secondname = CharField(max_length=100, null=True)
    date_of_birth = DateTimeField()
    created_at = DateTimeField(default=datetime.datetime.now)
    region = IntegerField()
    exe_production = TextField()
    details = TextField()
    subject = TextField()
    department = BigIntegerField()
    bailiff = TextField()
    ip_end = TextField()
