import datetime
import os

from dotenv import load_dotenv, find_dotenv
from peewee import Model, CharField, BooleanField, DateTimeField, IntegerField, TextField, \
    BigIntegerField, PostgresqlDatabase

load_dotenv(find_dotenv())

postgre_db = PostgresqlDatabase(database=os.environ.get("DATABASE_NAME"), user=os.environ.get("DATABASE_USER"),
                                password=os.environ.get("DATABASE_PASSWORD"),
                                host=os.environ.get("DATABASE_HOST"),
                                port=os.environ.get("DATABASE_PORT"), autoconnect=False)


class BaseModel(Model):
    class Meta:
        database = postgre_db


class NotCheckedHuman(BaseModel):
    name = CharField(max_length=100, null=False)
    lastname = CharField(max_length=100, null=False)
    secondname = CharField(max_length=100, null=True)
    region = IntegerField(null=True)
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
