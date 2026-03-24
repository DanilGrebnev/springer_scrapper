import datetime

from tortoise import fields
from tortoise.models import Model


class Request(Model):
    id = fields.IntField(primary_key=True)
    author: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User",
        related_name="requests",
        null=True,
        on_delete=fields.SET_NULL,
    )
    field_knowledge = fields.TextField(default="")
    target_theme = fields.TextField(default="")
    target_context = fields.TextField(default="")
    language = fields.CharField(max_length=50, default="")
    theme = fields.TextField(default="")
    date_from = fields.CharField(max_length=20, default="")
    date_to = fields.CharField(max_length=20, default="")
    open_access = fields.BooleanField(default=False)
    total_amount = fields.IntField(default=0)
    status = fields.CharField(max_length=50, default="process")
    error_detail = fields.TextField(default="")
    # Результаты, сформированные по этому запросу
    results: fields.ManyToManyRelation = fields.ManyToManyField(
        "models.ResultRequest",
        related_name="requests",
        through="request_result_requests",
    )
    datetime = fields.DatetimeField(default=datetime.datetime.now)

    class Meta:
        table = "requests"

    def __str__(self) -> str:
        return f"Request({self.pk}, {self.theme[:40]})"
