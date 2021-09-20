import datetime
import os

from peewee import Model, CharField, BooleanField, ForeignKeyField, DateTimeField, IntegerField, TextField, \
    BigIntegerField, PostgresqlDatabase

postgre_db = PostgresqlDatabase(database=os.environ.get("DATABASE_NAME"), user=os.environ.get("DATABASE_USER"),
                                password=os.environ.get("DATABASE_PASSWORD"),
                                host=os.environ.get("DATABASE_HOST"),
                                port=os.environ.get("DATABASE_PORT"), charset='utf8mb4', autoconnect=False)


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
