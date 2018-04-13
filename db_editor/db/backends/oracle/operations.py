from django.db.backends.oracle import operations
from django.db.backends.utils import truncate_name

from ....config import settings
from ....utils import string


class DatabaseOperations(operations.DatabaseOperations):
    def quote_name(self, name):
        if '.' in name:
            return '.'.join([
                super(DatabaseOperations, self).quote_name(term) 
                for term in name.split('.')
            ])
        return super(DatabaseOperations, self).quote_name(name)

    def _get_operation_name(self, prefix, table):
        """
        Get the operation (trigger, sequence, etc) name by
        replacing the table name prefix to a configured prefix
        """
        name_length = self.max_name_length() - 3
        return string.replace_prefix(
            truncate_name(table, name_length).upper(),
            settings.PREFIX.get('TABLE'),
            prefix
        )

    def _get_trigger_name(self, table):
        return self._get_operation_name(
            table=table,
            prefix=settings.PREFIX.get('TRIGGER'),
        )
        
    def _get_sequence_name(self, table):
        return self._get_operation_name(
            table=table,
            prefix=settings.PREFIX.get('SEQUENCE')
        )