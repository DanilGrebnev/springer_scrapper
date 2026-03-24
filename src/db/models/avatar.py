from tortoise import fields
from tortoise.models import Model


class Avatar(Model):
    id = fields.IntField(primary_key=True)
    file_object = fields.CharField(max_length=1024)
    type = fields.CharField(max_length=50, default="")
    size = fields.IntField(default=0)
    thumbnail = fields.CharField(max_length=1024, null=True)

    # Пользователь, которому принадлежит аватар
    user: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.User",
        related_name="avatars",
        null=True,
        on_delete=fields.CASCADE,
    )

    class Meta:
        table = "avatars"

    def __str__(self) -> str:
        return f"Avatar({self.pk})"
