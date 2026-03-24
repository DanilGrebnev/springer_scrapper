from tortoise import fields
from tortoise.models import Model


class ArticalMatch(Model):
    id = fields.IntField(primary_key=True)
    original_artical: fields.ForeignKeyRelation = fields.ForeignKeyField(
        "models.Article",
        related_name="matches",
        on_delete=fields.CASCADE,
    )
    level_match = fields.CharField(max_length=20, default="")
    comparison_of_rules = fields.JSONField(null=True)
    explanation = fields.TextField(default="")
    t_title = fields.CharField(max_length=1024, default="")
    t_abstract = fields.TextField(default="")

    class Meta:
        table = "artical_match"

    def __str__(self) -> str:
        return f"ArticalMatch({self.pk}, {self.level_match})"
