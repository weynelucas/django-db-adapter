from django.db.backends.oracle import schema as oracle

from ..base.schema import DatabaseSchemaEditor
from . import constants


class DatabaseSchemaEditor(DatabaseSchemaEditor, oracle.DatabaseSchemaEditor):
    sql_create_table = constants.SQL_CREATE_TABLE
    sql_create_check = constants.SQL_CREATE_CHECK
    sql_create_comment = constants.SQL_COMMENT_ON_COLUMN
    sql_create_pk = constants.SQL_CREATE_PK
    sql_create_fk = constants.SQL_CREATE_FK
    sql_create_index = constants.SQL_CREATE_INDEX
    sql_create_unique = constants.SQL_CREATE_UNIQUE
    sql_grant = constants.SQL_GRANT
    sql_comment_on_column = constants.SQL_COMMENT_ON_COLUMN

    sql_ending = ';\n/\n'
    sql_column_separator = ',\n    '

    data_type_check_term = {
        'BooleanField': '_bool',
        'NullBooleanField': '_bool',
        'PositiveIntegerField': '_gte',
        'PositiveSmallIntegerField': '_gte',
    }
