from db_adapter.settings import db_settings
from db_adapter.utils import split_table_identifiers


class DatabaseAdapterOperations:
    sql_create_sequence = None
    sql_create_trigger = None

    db_table_format = db_settings.DEFAULT_DB_TABLE_FORMAT

    obj_name_sequence = db_settings.DEFAULT_SEQUENCE_NAME
    obj_name_trigger = db_settings.DEFAULT_TRIGGER_NAME

    def autoinc_sql(self, table, column, **kwargs):
        if not self.sql_create_sequence and not self.sql_create_trigger:
            return None

        field = kwargs.get('field')
        minvalue, maxvalue = self.integer_field_ranges.get(
            field.get_internal_type() if field else 'AutoField'
        )

        args = {
            'sq_name': self._get_sequence_name(table, column=field.column),
            'sq_minvalue': minvalue,
            'sq_maxvalue': maxvalue,
            'tr_name': self._get_trigger_name(table, column=field.column),
            'tbl_name': self.quote_name(table),
            'col_name': self.quote_name(column),
        }

        sequence_sql = self.sql_create_sequence % args
        trigger_sql = self.sql_create_trigger % args
        return sequence_sql, trigger_sql

    def integer_field_range(self, internal_type: str):
        if internal_type in self.integer_field_ranges:
            return self.integer_field_ranges[internal_type]

        return None, None

    def _get_sequence_name(self, table, column=''):
        return self._object_name(
            table, pattern=self.obj_name_sequence, column=column
        ).upper()

    def _get_trigger_name(self, table, column=''):
        return self._object_name(
            table, pattern=self.obj_name_trigger, column=column
        ).upper()

    def _object_name(self, table, pattern, column=''):
        namespace, table, table_name = split_table_identifiers(
            table, self.db_table_format
        )

        name = pattern.format(
            table=table,
            table_name=table_name,
            columns=column,
            name='%s_%s' % (table_name, column) if column else table_name,
        )

        if namespace:
            return '"{}"."{}"'.format(namespace, name)

        return table
