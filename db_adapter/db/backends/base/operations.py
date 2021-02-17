from functools import lru_cache

from django.db.utils import ProgrammingError
from django.utils.functional import cached_property

from db_adapter.name_builders import ObjectNameBuilder
from db_adapter.utils import enforce_model, enforce_model_fields


class DatabaseOperations:
    sql_create_sequence = None
    sql_create_trigger = None

    name_builder_class = ObjectNameBuilder

    def autoinc_sql(self, table, column):
        if not self.sql_create_sequence and not self.sql_create_trigger:
            return None

        model, field = self._enforce_model_field_instances(table, column)

        args = {
            'sq_name': self._get_sequence_name(model, field),
            'tr_name': self._get_trigger_name(model, field),
            'tbl_name': self.quote_name(table),
            'col_name': self.quote_name(column),
        }

        try:
            _, max_value = self.integer_field_range(field.get_internal_type())
            args.update(sq_max_value=max_value)
        except KeyError:
            pass

        try:
            sequence_sql = self.sql_create_sequence % args
            trigger_sql = self.sql_create_trigger % args
            return sequence_sql, trigger_sql
        except KeyError as err:
            if 'sq_max_value' in err.args:
                raise ProgrammingError(
                    'Cannot retrieve the range of the column type bound to the '
                    'field %s' % field.name
                )

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
