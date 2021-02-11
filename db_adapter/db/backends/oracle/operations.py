from django.db.backends.oracle import operations as oracle

from ..base.operations import DatabaseAdapterOperations
from . import constants


class DatabaseOperations(DatabaseAdapterOperations, oracle.DatabaseOperations):
    sql_create_sequence = constants.SQL_CREATE_SEQUENCE
    sql_create_trigger = constants.SQL_CREATE_TRIGGER

    integer_field_ranges = {
        **oracle.DatabaseOperations.integer_field_ranges,
        'AutoField': (1, 99999999999),
        'BigAutoField': (1, 9999999999999999999),
    }

    def max_name_length(self):
        return None
