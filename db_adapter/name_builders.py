from typing import List

from django.db.models import Field, Model

from .settings import db_settings
from .utils import split_table_identifiers

Fields = List[Field]


class ObjectNameBuilder:
    default_db_table_pattern = db_settings.DEFAULT_DB_TABLE_PATTERN
    default_object_name_patterns = db_settings.DEFAULT_OBJECT_NAME_PATTERNS

    def process_name(
        self, model: Model, fields: Fields, type: str, qualifier=''
    ):
        parts = split_table_identifiers(
            model._meta.db_table,
            format=self.default_db_table_pattern,
        )
        table_parts_dict = dict(parts._asdict())
        namespace = table_parts_dict.pop('namespace', '')

        column_names = '_'.join([field.column for field in fields])
        name = (
            '%s_%s' % (parts.table_name, column_names)
            if column_names
            else parts.table_name
        )

        pattern = self.object_name_pattern(type)
        obj_name = pattern.format(
            **table_parts_dict,
            qualifier=qualifier,
            columns=column_names,
            name=name,
        )

        include_namespace = namespace and self.should_include_namespace(
            model, fields, type, qualifier
        )
        if include_namespace:
            return '"{}"."{}"'.format(namespace, obj_name)

        return obj_name

    def should_include_namespace(self, model, field, type, qualifier=''):
        return type in ['sequence', 'trigger', 'index']

    def object_name_pattern(self, type: str) -> str:
        return self.default_object_name_patterns[type.upper()]
