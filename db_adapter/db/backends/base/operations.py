from functools import lru_cache

import sqlparse

from django.db.utils import ProgrammingError
from django.utils.functional import cached_property

from db_adapter.settings import db_settings
from db_adapter.utils import enforce_model, enforce_model_fields


class DatabaseOperations:
    # Overrideable SQL statements
    sql_create_sequence = None
    sql_create_trigger = None
    sql_grant = 'GRANT %(privileges)s ON %(name)s TO %(role)s'

    # Setting variables
    role_name = db_settings.DEFAULT_ROLE_NAME
    name_builder_class = db_settings.NAME_BUILDER_CLASS
    default_object_privileges = db_settings.DEFAULT_OBJECT_PRIVILEGES
    sql_format_options = db_settings.SQL_FORMAT_OPTIONS

    def autoinc_sql(self, table, column):
        if not self.sql_create_sequence and not self.sql_create_trigger:
            return None

        model, field = self._enforce_model_field_instances(table, column)
        sequence_name = self._get_sequence_name(model, field)
        trigger_name = self._get_trigger_name(model, field)

        args = {
            'sq_name': sequence_name,
            'tr_name': trigger_name,
            'tbl_name': self.quote_name(table),
            'col_name': self.quote_name(column),
        }

        try:
            _, max_value = self.integer_field_range(field.get_internal_type())
            args.update(sq_max_value=max_value)
        except KeyError:
            pass

        try:
            sequence_sql = self._get_sequence_sql(sequence_name, args)
            trigger_sql = self.sql_create_trigger % args
            return [*sequence_sql, trigger_sql]
        except KeyError as err:
            if 'sq_max_value' in err.args:
                raise ProgrammingError(
                    'Cannot retrieve the range of the column type bound to the '
                    'field %s' % field.name
                )

    def control_sql(self, name, privileges=None):
        if not self.role_name:
            return None

        privileges = (
            self.default_object_privileges if privileges is None else privileges
        )

        return self.sql_grant % dict(
            name=self.quote_name(name),
            privileges=', '.join(privileges),
            role=self.quote_name(self.role_name),
        )

    def format_sql(self, sql, **kwargs):
        opts = {**self.sql_format_options, **kwargs}

        formatted = str(sql)

        if opts.pop('unquote', False):
            formatted = formatted.replace('"', '')

        return sqlparse.format(formatted, **opts)

    @cached_property
    def name_builder(self):
        return self.name_builder_class()

    @lru_cache(maxsize=None)
    def _enforce_model_field_instances(self, table, column=''):
        model = enforce_model(table)
        (field,) = enforce_model_fields(model, [column])

        return model, field

    def _get_sequence_name(self, table, column):
        model, field = self._enforce_model_field_instances(table, column)
        name = self.name_builder.process_name(model, [field], type='sequence')
        return self.quote_name(name)

    def _get_trigger_name(self, table, column=''):
        model, field = self._enforce_model_field_instances(table, column)
        name = self.name_builder.process_name(model, [field], type='trigger')
        return self.quote_name(name)

    def _get_sequence_sql(self, name, args):
        sequence_sql = [self.sql_create_sequence % args]

        grant_sql = self.control_sql(name, privileges=['SELECT'])
        if grant_sql:
            sequence_sql.append(grant_sql)

        return sequence_sql
