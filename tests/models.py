from django.db import models


class DBAdapterModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """

    class Meta:
        app_label = 'tests'
        abstract = True


class Reporter(DBAdapterModel):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)

    class Meta:
        db_table = '"tests"."tbl_reporter"'
        abstract = True


class Tag(DBAdapterModel):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(
        null=True, help_text='Optional description for tag'
    )

    class Meta:
        db_table = 'tbl_tag'


class Author(DBAdapterModel):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'tbl_author'


class Post(DBAdapterModel):
    name = models.CharField(max_length=30, null=True)
    text = models.TextField()
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        db_column='written_by',
    )
    tag = models.ForeignKey(Tag, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = 'tbl_post'


class Square(DBAdapterModel):
    side = models.PositiveIntegerField(null=True)

    class Meta:
        db_table = 'tbl_square'


class Article(DBAdapterModel):
    article_id = models.BigAutoField(primary_key=True)
    name = models.CharField(max_length=30)
    text = models.TextField(null=True, help_text='Article description')
    active = models.NullBooleanField()
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        null=True,
        db_index=False,
        db_column='written_by',
    )
    tag = models.ForeignKey(
        Tag,
        on_delete=models.CASCADE,
        null=True,
        db_index=True,
    )

    class Meta:
        db_table = 'tbl_article'
        unique_together = ['author', 'name']
