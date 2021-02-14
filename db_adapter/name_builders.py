from functools import lru_cache
from typing import List

from django.db.models import Field, Model
from django.utils.functional import cached_property

from .settings import db_settings
from .utils import split_table_identifiers

Fields = List[Field]


class ObjectNameBuilder:
    default_db_settings = db_settings

    def __init__(self, settings=None):
        self.settings = settings or self.default_db_settings

    def process_name(
        self,
        model: Model,
        fields: Fields,
        type: str,
        qualifier='',
        include_namespace=True,
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

        obj_name = self.object_type_name_formats[type].format(
            **table_parts_dict,
            qualifier=qualifier,
            columns=column_names,
            name=name,
        )

        if namespace and include_namespace:
            return '"{}"."{}"'.format(namespace, obj_name)

        return obj_name

    @cached_property
    def object_type_name_formats(self):
        return {
            'sequence': self.settings.DEFAULT_SEQUENCE_NAME,
            'trigger': self.settings.DEFAULT_TRIGGER_NAME,
            'index': self.settings.DEFAULT_INDEX_NAME,
            'primary_key': self.settings.DEFAULT_PRIMARY_KEY_NAME,
            'foreign_key': self.settings.DEFAULT_FOREIGN_KEY_NAME,
            'unique': self.settings.DEFAULT_UNIQUE_NAME,
            'check': self.settings.DEFAULT_CHECK_NAME,
        }

    @cached_property
    def db_table_format(self) -> str:
        return self.settings.DEFAULT_DB_TABLE_FORMAT
