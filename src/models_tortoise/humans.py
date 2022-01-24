import datetime

from tortoise import Model, fields


class NotCheckedHuman(Model):
    id = fields.IntField(index=True, pk=True)
    name = fields.CharField(max_length=100, null=False)
    lastname = fields.CharField(max_length=100, null=False)
    secondname = fields.CharField(max_length=100, null=True)
    birth_date = fields.DatetimeField(null=True)
    is_checked = fields.BooleanField(default=False, null=False)
    being_check = fields.BooleanField(default=False, null=False)

    class Meta:
        table = "notcheckedhuman"


class FSSPHuman(Model):
    name = fields.TextField(null=False)
    created_at = fields.DatetimeField(default=datetime.datetime.now)
    region = fields.IntField(null=True)
    exe_production = fields.TextField(null=True)
    details = fields.TextField(null=True)
    subject = fields.TextField(null=True)
    department = fields.TextField(null=True)
    bailiff = fields.TextField(null=True)
    ip_end = fields.TextField(null=True)

    class Meta:
        table = "fssphuman"
