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
