from collections import namedtuple
from typing import List, Union

from parse import compile, parse

from django.apps import apps
from django.db.backends.utils import split_identifier
from django.db.models import Field, Model

TableIdentifiers = namedtuple(
    'TableIdentifiers', ['namespace', 'table', 'table_name']
)


def split_table_identifiers(db_table, format='') -> TableIdentifiers:
    namespace, table = split_identifier(db_table)

    groupdict = dict(
        namespace=namespace,
        table=table,
        table_name=table,
    )

    if format:
        _, table_format = split_identifier(format)

        result = parse(table_format, table)
        if result:
            groupdict.update(result.named)

    return TableIdentifiers(**groupdict)


def normalize_table(db_table: str, format: str, exclude=[]):
    # Ignore excluded formats
    for fmt in exclude:
        result = parse(fmt, db_table)
        if result:
            return db_table

    namespace, table_name = split_identifier(db_table)
    namespace_format, table_format = split_identifier(format)

    # Add namespace from format when specified, but not included in db_table
    if namespace_format and not namespace:
        result = parse(table_format, table_name)
        formatted = table_name
        if not result:
            formatted = table_format.format(table_name=table_name)
        return '"{}"."{}"'.format(namespace_format, formatted)

    pattern = compile(format)
    result = pattern.parse(db_table)
    if not result:
        return format.format(table_name=db_table)

    return db_table


Fields = List[Field]
FieldsOrColumns = Union[Fields, List[str]]
ModelOrTableName = Union[Model, str]


def enforce_model(model_or_table_name: ModelOrTableName):
    model = model_or_table_name
    if isinstance(model, str):
        model = next(
            (m for m in apps.get_models() if m._meta.db_table == model),
            None,
        )

    return model


def enforce_model_fields(model: Model, items: FieldsOrColumns = []) -> Fields:
    def enforce(field_or_column):
        if isinstance(field_or_column, str):
            return next(
                filter(
                    lambda f: f.column == field_or_column,
                    model._meta.local_fields,
                )
            )
        return field_or_column

    return list(map(enforce, items))
