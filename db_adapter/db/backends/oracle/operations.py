from django.db.backends.oracle import operations as oracle

from ..base.operations import DatabaseOperations
from . import constants


class DatabaseOperations(DatabaseOperations, oracle.DatabaseOperations):
    sql_create_sequence = constants.SQL_CREATE_SEQUENCE
    sql_create_trigger = constants.SQL_CREATE_TRIGGER
    sql_grant = constants.SQL_GRANT

    integer_field_ranges = {
        **oracle.DatabaseOperations.integer_field_ranges,
        'SmallAutoField': (-99999, 99999),
        'AutoField': (-99999999999, 99999999999),
        'BigAutoField': (-9999999999999999999, 9999999999999999999),
    }

    def max_name_length(self):
        return None
