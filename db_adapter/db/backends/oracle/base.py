from django.db.backends.oracle import base

from .operations import DatabaseOperations
from .schema import DatabaseSchemaEditor


class DatabaseWrapper(base.DatabaseWrapper):
    SchemaEditorClass = DatabaseSchemaEditor

    def __init__(self, *args, **kwargs):
        super(DatabaseWrapper, self).__init__(*args, *kwargs)
        self.ops = DatabaseOperations(self)