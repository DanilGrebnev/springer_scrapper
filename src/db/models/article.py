import datetime

from tortoise import fields
from tortoise.models import Model


class Article(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=1024, default="")
    link = fields.CharField(max_length=2048, default="")
    description = fields.TextField(default="")
    abstract = fields.TextField(default="")
    publications_type = fields.CharField(max_length=100, default="")
    authors = fields.TextField(default="")
    published = fields.CharField(max_length=100, default="")
    open_access = fields.BooleanField(default=False)
    publish_name = fields.CharField(max_length=512, default="")
    publish_link = fields.CharField(max_length=2048, default="")
    citation = fields.TextField(default="")
    datetime = fields.DatetimeField(default=datetime.datetime.now)

    class Meta:
        table = "articles"

    def __str__(self) -> str:
        return f"Article({self.pk}, {self.title[:60]})"
