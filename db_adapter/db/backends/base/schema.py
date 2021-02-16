import logging
from typing import OrderedDict, Tuple

from django.db.models import Field, Model
from django.db.transaction import TransactionManagementError

from db_adapter.settings import db_settings
from db_adapter.utils import enforce_model, enforce_model_fields

logger = logging.getLogger('django.db.backends.schema')


class DatabaseSchemaEditor:
    """
    This class and its subclasses are responsible for emitting schema-changing
    statements to the databases - model creation/removal/alteration, field
    renaming, index fiddling, and so on.
    """

    # Deferred column SQL order
    deferred_sql_order = (
        'PRIMARY KEY',
        'UNIQUE',
        'FOREIGN KEY',
        'CHECK',
        'INDEX',
        'COMMENT',
        'SEQUENCE',
        'TRIGGER',
    )

    # Overrideable SQL templates
    sql_comment_on_column = (
        'COMMENT ON COLUMN %(table)s.%(column)s IS "%(comment)s"'
    )

    # Executable SQL definitions
    sql_ending = ';'
    sql_column_separator = ', '

    # Mapping of index name suffix to their database object types
    suffix_object_types = {
        '_check': 'check',
        '_pk': 'primary_key',
        '_fk': 'foreign_key',
        '_uniq': 'unique',
        '_idx': 'index',
    }

    name_builder_class = db_settings.DEFAULT_NAME_BUILDER_CLASS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Init deferred column SQL dict
        self.deferred_column_sql = OrderedDict(
            [(item, []) for item in self.deferred_sql_order]
        )
        self.deferred_table_sql = OrderedDict(
            [(item, []) for item in self.deferred_sql_order]
        )

    def execute(self, sql, params=()):
        """Execute the given SQL statement, with optional parameters."""
        # Don't perform the transactional DDL check if SQL is being collected
        # as it's not going to be executed anyway.
        if (
            not self.collect_sql
            and self.connection.in_atomic_block
            and not self.connection.features.can_rollback_ddl
        ):
            raise TransactionManagementError(
                "Executing DDL statements while in a transaction on databases "
                "that can't perform a rollback is prohibited."
            )
        # Account for non-string statement objects.
        sql = str(sql)
        # Log the command we're running, then run it
        logger.debug(
            "%s; (params %r)", sql, params, extra={'params': params, 'sql': sql}
        )
        if self.collect_sql:
            ending = '' if sql.endswith(self.sql_ending) else self.sql_ending
            if params is not None:
                self.collected_sql.append(
                    (sql % tuple(map(self.quote_value, params))) + ending
                )
            else:
                self.collected_sql.append(sql + ending)
        else:
            with self.connection.cursor() as cursor:
                cursor.execute(sql, params)

    def column_sql(
        self, model: Model, field: Field, include_default=False
    ) -> Tuple[str, list]:
        # Get the column's type and use that as the basis of the SQL
        db_params = field.db_parameters(connection=self.connection)
        sql = db_params['type']
        params = []

        # Check for fields that aren't actually columns (e.g. M2M)
        if sql is None:
            return None, None

        if field.null and not self.connection.features.implied_column_null:
            sql += ' NULL'

        # Check constraints
        if not field.null:
            check = '%s IS NOT NULL' % field.column
            self.deferred_column_sql['CHECK'].append(
                self._create_check_sql_for_field(
                    model, field, check, qualifier='_nn'
                )
            )

        db_params = field.db_parameters(connection=self.connection)
        if db_params['check']:
            self.deferred_column_sql['CHECK'].append(
                self._create_check_sql_for_field(
                    model, field, db_params['check']
                )
            )

        # Primary/unique keys
        if field.primary_key:
            self.deferred_column_sql['PRIMARY KEY'].append(
                self._create_primary_key_sql(model, field)
            )
        elif field.unique:
            self.deferred_column_sql['UNIQUE'].append(
                self._create_unique_sql(model, [field.column])
            )

        # FK
        if field.remote_field and field.db_constraint:
            self.deferred_column_sql['FOREIGN KEY'].append(
                self._create_fk_sql(
                    model, field, suffix='_fk_%(to_table)s_%(to_column)s'
                )
            )

        # Comment columns for fields with help_tex
        if field.help_text:
            self.deferred_column_sql['COMMENT'].append(
                self._create_comment_sql(model, field)
            )

        return sql, params

    def table_sql(self, model: Model) -> Tuple[str, list]:
        column_sqls = []
        params = []

        for field in model._meta.local_fields:
            definition, extra_params = self.column_sql(model, field, False)
            if definition is None:
                continue

            params.extend(extra_params)
            column_sqls.append(
                '%s %s'
                % (
                    self.quote_name(field.column),
                    definition,
                )
            )

        sql = self.sql_create_table % dict(
            table=self.quote_name(model._meta.db_table),
            definition=self.sql_column_separator.join(column_sqls),
        )

        # Add any unique_togethers (always deferred, as some fields might be
        # created afterwards, like geometry fields with some backends)
        for fields in model._meta.unique_together:
            columns = [model._meta.get_field(field).column for field in fields]
            self.deferred_table_sql['UNIQUE'].append(
                self._create_unique_sql(model, columns)
            )

        # Add any field index and index_together's (deferred as SQLite3
        # _remake_table needs it)
        self.deferred_table_sql['INDEX'].extend(self._model_indexes_sql(model))

        return sql, params

    def create_model(self, model: Model):
        sql, params = self.table_sql(model)

        if sql:
            self.execute(sql, params or None)

        for item in self.deferred_sql_order:
            sql_column = self.deferred_column_sql[item]
            sql_table = self.deferred_table_sql[item]

            self.deferred_sql.extend(sql_column)
            self.deferred_sql.extend(sql_table)

    def _model_autoincs_sql(self, model: Model):
        output = []
        for field in model._meta.local_fields:
            if field.get_internal_type() in ('AutoField', 'BigAutoField'):
                autoinc_sql = self.connection.ops.autoinc_sql(
                    model._meta.db_table, field.column, model=model, field=field
                )
                if autoinc_sql:
                    output.extend(autoinc_sql)

            return output

    def _create_check_sql_for_field(self, model, field, check, qualifier=''):
        if not qualifier:
            data_type_check_constraints_suffixes = getattr(
                self.connection, 'data_type_check_constraints_suffixes', {}
            )
            qualifier = data_type_check_constraints_suffixes.get(
                field.get_internal_type(), ''
            )

        constraint_name = self._create_index_name(
            model,
            [field.column],
            suffix='_check',
            qualifier=qualifier,
        )

        return self._create_check_sql(model, constraint_name, check)

    def _create_check_sql(self, model: Model, name, check):
        return self.sql_create_check % dict(
            table=self.quote_name(model._meta.db_table),
            name=self.quote_name(name),
            check=check,
        )

    def _create_primary_key_sql(self, model: Model, field: Field):
        return self.sql_create_pk % dict(
            table=self.quote_name(model._meta.db_table),
            name=self.quote_name(
                self._create_index_name(
                    model._meta.db_table, [field.column], suffix='_pk'
                )
            ),
            columns=self.quote_name(field.column),
        )

    def _create_comment_sql(self, model: Model, field: Field):
        return self.sql_comment_on_column % dict(
            table=self.quote_name(model._meta.db_table),
            column=self.quote_name(field.column),
            comment=field.help_text,
        )

    def _create_index_sql(self, model, fields, suffix='_idx', **kwargs):
        return super()._create_index_sql(model, fields, suffix=suffix, **kwargs)

    def _create_index_name(
        self, model_or_table_name, column_names, suffix='_idx', qualifier=''
    ):
        suffix = suffix and '_'.join(suffix.split('_')[:2])
        type = self.suffix_object_types[suffix]

        model = enforce_model(model_or_table_name)
        fields = enforce_model_fields(model, column_names)

        name_builder = self.name_builder_class()
        name = name_builder.process_name(model, fields, type, qualifier)
        return self.quote_name(name)
