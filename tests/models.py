from django.db import models


class DBAdapterModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """

    class Meta:
        app_label = 'tests'
        abstract = True


class BasicModel(DBAdapterModel):
    text = models.CharField(
        max_length=100,
        db_column='vl_text',
        verbose_name='Text comes here',
        help_text='Text description',
    )

    class Meta:
        db_table = 'tbl_basic'


class ForeignKeyTarget(DBAdapterModel):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = 'tbl_fk_target'


class ForeignKeySource(DBAdapterModel):
    name = models.CharField(max_length=100)
    target = models.ForeignKey(
        ForeignKeyTarget,
        related_name='sources',
        help_text='Target',
        verbose_name='Target',
        on_delete=models.CASCADE,
        db_column='target_id',
    )

    class Meta:
        db_table = 'tbl_fk_src'


class NamespacedAbstractModel(DBAdapterModel):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = '"db_adapter"."tbl_namespaced"'
        abstract = True
