from django.db import models


class DBAdapterModel(models.Model):
    """
    Base for test models that sets app_label, so they play nicely.
    """

    class Meta:
        app_label = 'tests'
        abstract = True


class BasicModel(DBAdapterModel):
    id = models.AutoField(primary_key=True)
    text = models.CharField(
        max_length=100,
        db_column='vl_text',
        verbose_name='Text comes here',
        help_text='Text description',
    )

    class Meta:
        db_table = 'tbl_basic_model'


class NamespacedAbstractModel(DBAdapterModel):
    name = models.CharField(max_length=100)

    class Meta:
        db_table = '"db_adapter"."tbl_namespaced_model"'
        abstract = True
