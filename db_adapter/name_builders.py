from typing import List

from django.db.models import Field, Model

from .settings import db_settings
from .utils import split_table_identifiers


class ObjectNameBuilder:
    db_table_format = db_settings.DEFAULT_DB_TABLE_FORMAT
    obj_type_formats = {
        'sequence': db_settings.DEFAULT_SEQUENCE_NAME,
        'trigger': db_settings.DEFAULT_TRIGGER_NAME,
        'index': db_settings.DEFAULT_INDEX_NAME,
        'primary_key': db_settings.DEFAULT_PRIMARY_KEY_NAME,
        'foreign_key': db_settings.DEFAULT_FOREIGN_KEY_NAME,
        'unique': db_settings.DEFAULT_UNIQUE_NAME,
        'check': db_settings.DEFAULT_CHECK_NAME,
    }

    def process_name(
        self, model: Model, fields: List[Field], type='', qualifier=''
    ):
        parts = split_table_identifiers(
            model._meta.db_table,
            format=self.db_table_format,
        )
        table_parts_dict = dict(parts._asdict())
        namespace = table_parts_dict.pop('namespace', '')

        column_names = '_'.join([field.column for field in fields])
        name = (
            '%s_%s' % (parts.table_name, column_names)
            if column_names
            else parts.table_name
        )

        obj_name = self.obj_type_formats[type].format(
            **table_parts_dict,
            qualifier=qualifier,
            columns=column_names,
            name=name,
        )

        if namespace:
            return '"{}"."{}"'.format(namespace, obj_name)

        return obj_name
