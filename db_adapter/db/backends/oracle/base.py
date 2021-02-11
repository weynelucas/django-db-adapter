from django.db.backends.oracle import base as oracle

from . import operations, schema


class DatabaseWrapper(oracle.DatabaseWrapper):
    SchemaEditorClass = schema.DatabaseSchemaEditor
    ops_class = operations.DatabaseOperations

    data_types = {
        **oracle.DatabaseWrapper.data_types,
        'AutoField': 'NUMBER(11)',
        'BigAutoField': 'NUMBER(19)',
    }
    data_type_check_constraints = {
        'BooleanField': '%(qn_column)s IN (0,1)',
        'NullBooleanField': '%(qn_column)s IN (0,1)',
        'PositiveIntegerField': '%(qn_column)s >= 0',
        'PositiveSmallIntegerField': '%(qn_column)s >= 0',
    }
    data_type_check_constraints_suffixes = {
        'BooleanField': '_bool',
        'NullBooleanField': '_bool',
        'PositiveIntegerField': '_gte',
        'PositiveSmallIntegerField': '_gte',
    }
