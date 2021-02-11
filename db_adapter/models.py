from django.db.models import Model

from .utils import normalize_table


def apply_db_table_normalization(sender: Model, **kwargs):
    from .settings import db_settings

    should_normalize = (
        db_settings.ENABLE_DB_TABLE_NORMALIZATION
        and db_settings.DEFAULT_DB_TABLE_FORMAT
    )

    if should_normalize:
        normalized_name = normalize_table(
            sender._meta.db_table,
            format=db_settings.DEFAULT_DB_TABLE_FORMAT,
            exclude=db_settings.IGNORE_DB_TABLE_FORMATS,
        )

        sender._meta.db_table = normalized_name
