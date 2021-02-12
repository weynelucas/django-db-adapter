import logging
from typing import Tuple

from django.db.models import Field, Model
from django.db.transaction import TransactionManagementError

from db_adapter.settings import db_settings
from db_adapter.utils import split_table_identifiers

logger = logging.getLogger('django.db.backends.schema')


class DatabaseAdapterSchemaEditor:
    # Overrideable SQL templates
    sql_comment_on_column = (
        'COMMENT ON COLUMN %(table)s.%(column)s is "%(comment)s"'
    )

    # Executable SQL definitions
    sql_ending = ';'
    sql_column_separator = ','

    # Check constraints definitions
    data_type_check_qualifier = {}
    sql_chek_not_null_qualifier = '_nn'
    sql_check_not_null = 'IS NOT NULL'

    db_table_format = db_settings.DEFAULT_DB_TABLE_FORMAT

    # Database objects naming patterns
    obj_name_index = db_settings.DEFAULT_INDEX_NAME
    obj_name_pk = db_settings.DEFAULT_PRIMARY_KEY_NAME
    obj_name_fk = db_settings.DEFAULT_FOREIGN_KEY_NAME
    obj_name_unique = db_settings.DEFAULT_UNIQUE_NAME
    obj_name_check = db_settings.DEFAULT_CHECK_NAME

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
        return sql, params

    def create_model(self, model: Model):
        sql, params = self.table_sql(model)

        if sql:
            self.execute(sql, params or None)

        self.deferred_sql.extend(self._model_pks_sql(model))
        self.deferred_sql.extend(self._model_uniques_sql(model))
        self.deferred_sql.extend(self._model_fks_sql(model))
        self.deferred_sql.extend(self._model_checks_sql(model))
        self.deferred_sql.extend(self._model_indexes_sql(model))
        self.deferred_sql.extend(self._model_col_comments_sql(model))
        self.deferred_sql.extend(self._model_autoincs_sql(model))

    def _model_pks_sql(self, model: Model):
        """
        Return a list of all primary key constraints SQL statements for the
        specified model.
        """
        output = []
        for field in model._meta.local_fields:
            if field.primary_key:
                output.append(self._create_pk_sql(model, field))

        return output

    def _model_uniques_sql(self, model: Model):
        """
        Return a list of all unique constraints SQL statements (unique or
        unique_together) for the specified model.
        """
        output = []
        for field in model._meta.local_fields:
            if field.unique and not field.primary_key:
                output.append(self._create_unique_sql(model, [field.column]))

        for fields in model._meta.unique_together:
            columns = [model._meta.get_field(field).column for field in fields]
            output.append(self._create_unique_sql(model, columns))

        return output

    def _model_fks_sql(self, model: Model):
        """
        Return a list of all foreign key constraints SQL statements for the
        specified model.
        """
        output = []
        for field in model._meta.local_fields:
            if field.remote_field and field.db_constraint:
                output.append(self._create_fk_sql(model, field))

        return output

    def _model_checks_sql(self, model: Model):
        output = []
        for field in model._meta.local_fields:
            db_params = field.db_parameters(connection=self.connection)

            if not field.null:
                constraint_name = self._create_object_name(
                    model,
                    [field.column],
                    pattern=self.obj_name_check,
                    qualifier='_nn',
                )
                check = '%(qn_column)s IS NOT NULL' % dict(
                    qn_column=self.quote_name(field.column)
                )
                output.append(
                    self._create_check_sql(model, constraint_name, check)
                )

            if db_params['check']:
                qualifier = self.data_type_check_qualifier.get(
                    field.get_internal_type(), ''
                )
                constraint_name = self._create_object_name(
                    model,
                    [field.column],
                    pattern=self.obj_name_check,
                    qualifier=qualifier,
                )
                output.append(
                    self._create_check_sql(
                        model, constraint_name, db_params['check']
                    )
                )

        return output

    def _model_col_comments_sql(self, model: Model):
        """
        Return a list of all column comments SQL statements (from fields
        help_text) for the specified model.
        """
        output = []
        for field in model._meta.local_fields:
            if field.help_text:
                sql = self.sql_comment_on_column % dict(
                    table=self.quote_name(model._meta.db_table),
                    column=self.quote_name(field.column),
                    comment=field.help_text,
                )
                output.append(sql)

        return output

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

    def _create_object_name(
        self, model: Model, columns: list, pattern, qualifier=''
    ):
        _, table, table_name = split_table_identifiers(
            model._meta.db_table, self.db_table_format
        )
        column_names = '_'.join(columns)

        return pattern.format(
            table=table,
            table_name=table_name,
            columns=column_names,
            name='%s_%s' % (table_name, column_names),
            qualifier=qualifier,
        )

    def _create_index_sql(self, model, fields, suffix='', sql=None):
        """
        Return the SQL statement to create the index for one or several fields.
        `sql` can be specified if the syntax differs from the standard (GIS
        indexes, ...).
        """
        tablespace_sql = self._get_index_tablespace_sql(model, fields)
        columns = [field.column for field in fields]
        sql_create_index = sql or self.sql_create_index
        return sql_create_index % dict(
            table=self.quote_name(model._meta.db_table),
            name=self.quote_name(
                self._create_object_name(
                    model, columns, pattern=self.obj_name_index
                )
            ),
            using='',
            columns=', '.join(self.quote_name(column) for column in columns),
            extra=tablespace_sql,
        )

    def _create_fk_sql(self, model: Model, field: Field, **kwargs):
        from_table = model._meta.db_table
        from_column = field.column
        to_column = field.target_field.column

        return self.sql_create_fk % dict(
            table=self.quote_name(from_table),
            name=self._fk_constraint_name(model, field),
            column=self.quote_name(from_column),
            to_table=self.quote_name(field.target_field.model._meta.db_table),
            to_column=self.quote_name(to_column),
            deferrable=self.connection.ops.deferrable_sql(),
        )

    def _fk_constraint_name(self, model: Model, field: Field, **kwargs) -> str:
        return self.quote_name(
            self._create_object_name(
                model, [field.column], pattern=self.obj_name_fk
            )
        )

    def _create_pk_sql(self, model: Model, field: Field):
        table = self.quote_name(model._meta.db_table)
        name = self._pk_constraint_name(model, field)
        column = self.quote_name(field.column)
        return self.sql_create_pk % dict(
            table=table,
            name=name,
            columns=column,
        )

    def _pk_constraint_name(self, model: Model, field: Field):
        return self.quote_name(
            self._create_object_name(
                model, [field.column], pattern=self.obj_name_pk
            )
        )

    def _create_unique_sql(self, model, columns, name=None, condition=None):
        table = self.quote_name(model._meta.db_table)
        if name is None:
            name = self._unique_constraint_name(model, columns)
        else:
            name = self.quote_name(name)

        if condition:
            return self.sql_create_unique_index % dict(
                table=table,
                name=name,
                columns=columns,
                condition=' WHERE ' + condition,
            )

        return self.sql_create_unique % dict(
            table=table,
            name=name,
            columns=', '.join(self.quote_name(column) for column in columns),
        )

    def _unique_constraint_name(self, model: Model, columns: list):
        return self.quote_name(
            self._create_object_name(
                model, columns, pattern=self.obj_name_unique
            )
        )
