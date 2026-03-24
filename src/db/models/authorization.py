import datetime

from tortoise import fields
from tortoise.models import Model


class Authorization(Model):
    id = fields.IntField(primary_key=True)
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User",
        related_name="authorizations",
        on_delete=fields.CASCADE,
    )
    type_auth = fields.CharField(max_length=50, default="")
    google_data = fields.JSONField(null=True)
    count_uses = fields.IntField(default=0)
    hash_refresh_token = fields.CharField(max_length=128, null=True)
    refresh_expires_at = fields.DatetimeField(null=True)
    logout_datetime = fields.DatetimeField(null=True)
    datetime = fields.DatetimeField(default=datetime.datetime.now)

    class Meta:
        table = "authorizations"

    def __str__(self) -> str:
        return f"Authorization({self.pk}, {self.type_auth})"
