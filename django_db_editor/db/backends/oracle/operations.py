from django.conf import settings
from django.db.backends.oracle import operations
from django.db.backends.utils import truncate_name

from .utils import without_prefix, get_owner_prefix
from ....utils import string, db_options


class DatabaseOperations(operations.DatabaseOperations):
    def quote_name(self, name):
        if '.' in name:
            return '.'.join([super(DatabaseOperations, self).quote_name(term) for term in name.split('.')])
        return super(DatabaseOperations, self).quote_name(name)

    def _get_operation_name(self, prefix, table):
        name_length = self.max_name_length() - 3
        table = without_prefix(truncate_name(table, name_length).upper())
        return '{0}{1}'.format(prefix, table)

    def _get_trigger_name(self, table):
        return self._get_operation_name(
            table=table,
            prefix=db_options.get_prefix('trigger').upper()
        )
        
    def _get_sequence_name(self, table):
        return self._get_operation_name(
            table=table,
            prefix=db_options.get_prefix('sequence').upper()
        )