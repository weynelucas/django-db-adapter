from django.db.models import Model
from django.db.models.signals import class_prepared, pre_init

from .settings import db_settings
from .utils import normalize_table


def apply_db_table_normalization(sender: Model, **kwargs):
    normalized_name = normalize_table(
        sender._meta.db_table,
        format=db_settings.DEFAULT_DB_TABLE_FORMAT,
        exclude=db_settings.IGNORE_DB_TABLE_FORMATS,
    )

    sender._meta.db_table = normalized_name


if (
    db_settings.ENABLE_DB_TABLE_NORMALIZATION
    and db_settings.DEFAULT_DB_TABLE_FORMAT
):
    pre_init.connect(apply_db_table_normalization)
    class_prepared.connect(apply_db_table_normalization)
