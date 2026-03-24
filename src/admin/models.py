"""
Stub-модель администратора.
Расширяется другим чатом: добавляются поля, связи, дополнительные таблицы.
AbstractAdmin предоставляет только: id, username, password.
"""
import datetime

from tortoise import fields
from fastapi_admin.models import AbstractAdmin


class Admin(AbstractAdmin):
    last_login = fields.DatetimeField(default=datetime.datetime.now, null=True)
    email = fields.CharField(max_length=200, default="")

    class Meta:
        table = "admin"

    def __str__(self) -> str:
        return f"{self.pk}#{self.username}"
