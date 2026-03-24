import datetime

from tortoise import fields
from tortoise.models import Model


class User(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255, default="")
    last_name = fields.CharField(max_length=255, default="")
    username = fields.CharField(max_length=255, unique=True)
    password = fields.CharField(max_length=512)
    status = fields.CharField(max_length=50, default="active")
    email = fields.CharField(max_length=255, unique=True, default="")
    refresh_token = fields.CharField(max_length=512, null=True)
    hash_refresh_token = fields.CharField(max_length=512, null=True)
    balance = fields.FloatField(default=5.0)
    datetime = fields.DatetimeField(default=datetime.datetime.now)

    # Обратные связи (объявляются в других моделях через FK)
    # avatars: ReverseRelation[Avatar]
    # requests: ReverseRelation[Request]
    # receipts: ReverseRelation[Receipt]
    # authorizations: ReverseRelation[Authorization]

    class Meta:
        table = "users"

    def __str__(self) -> str:
        return f"{self.pk}#{self.username}"
