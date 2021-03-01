from django.db.models import Model
from django.db.models.signals import class_prepared, pre_init

from .utils import normalize_table


def transform_db_table(sender: Model, **kwargs):
    from .settings import db_settings

    should_transform = (
        db_settings.ENABLE_TRANSFORM_DB_TABLE
        and db_settings.DEFAULT_DB_TABLE_PATTERN
    )

    if should_transform:
        normalized_name = normalize_table(
            sender._meta.db_table,
            format=db_settings.DEFAULT_DB_TABLE_PATTERN,
            exclude=db_settings.IGNORE_DB_TABLE_PATTERNS,
        )

        sender._meta.db_table = normalized_name


pre_init.connect(transform_db_table)
class_prepared.connect(transform_db_table)
