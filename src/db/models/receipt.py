import datetime

from tortoise import fields
from tortoise.models import Model


class Receipt(Model):
    id = fields.IntField(primary_key=True)
    payment_datetime = fields.DatetimeField(null=True)
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User",
        related_name="receipts",
        null=True,
        on_delete=fields.SET_NULL,
    )
    status = fields.CharField(max_length=50, default="pending")
    price = fields.FloatField(default=0.0)
    # Запросы, оплаченные этим чеком
    requests: fields.ManyToManyRelation = fields.ManyToManyField(
        "models.Request",
        related_name="receipts",
        through="receipt_requests",
    )
    datetime = fields.DatetimeField(default=datetime.datetime.now)

    class Meta:
        table = "receipts"

    def __str__(self) -> str:
        return f"Receipt({self.pk}, {self.status})"
