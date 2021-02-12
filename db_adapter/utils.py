from collections import namedtuple

from parse import compile, parse

from django.db.backends.utils import split_identifier

# from .settings import db_settings


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
