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
    date_of_birth = DateTimeField(null=True)
    city_info = TextField(null=True)
    created_at = DateTimeField(default=datetime.datetime.now)
    region = IntegerField(null=True)
    exe_production = TextField(null=True)
    details = TextField(null=True)
    subject = TextField(null=True)
    department = TextField(null=True)
    bailiff = TextField(null=True)
    ip_end = TextField(null=True)
