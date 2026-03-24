from tortoise import fields
from tortoise.models import Model


class ResultRequest(Model):
    id = fields.IntField(primary_key=True)
    articles: fields.ManyToManyRelation = fields.ManyToManyField(
        "models.ArticalMatch",
        related_name="result_requests",
        through="result_request_artical_matches",
    )
    prompt_tokens = fields.IntField(default=0)
    completion_tokens = fields.IntField(default=0)
    total_tokens = fields.IntField(default=0)
    response_model = fields.CharField(max_length=100, default="")

    class Meta:
        table = "result_requests"

    def __str__(self) -> str:
        return f"ResultRequest({self.pk}, tokens={self.total_tokens})"
