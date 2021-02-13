import logging
from typing import List, Tuple, Union

from django.db.models import Field, Model
from django.db.transaction import TransactionManagementError

from db_adapter.settings import db_settings

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
                output.append(self._create_unique_sql(model, [field]))

        for fields in model._meta.unique_together:
            fields = [model._meta.get_field(field) for field in fields]
            output.append(self._create_unique_sql(model, fields))

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
                constraint_name = self._check_constraint_name(
                    model, field, qualifier='_nn'
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
                constraint_name = self._check_constraint_name(
                    model, field, qualifier=qualifier
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
        self,
        model: Model,
        fields: Union[List[Field], List[str]],
        type: str,
        **kwargs,
    ):
        def enforce_model_field(field_or_column_name):
            """
            Workaround function to work with Dajngo version wher the backend
            provide the list of column names instead model fields
            """
            if isinstance(field_or_column_name, str):
                return next(
                    filter(
                        lambda field: field.column == field_or_column_name,
                        model._meta.local_fields,
                    )
                )

            return field_or_column_name

        fields = map(enforce_model_field, fields)

        builder = self._get_name_builder()
        name = builder.process_name(model, fields, type, **kwargs)

        return self.quote_name(name)

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
            name=self._create_object_name(model, columns, type='index'),
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

    def _create_pk_sql(self, model: Model, field: Field):
        table = self.quote_name(model._meta.db_table)
        name = self._pk_constraint_name(model, field)
        column = self.quote_name(field.column)
        return self.sql_create_pk % dict(
            table=table,
            name=name,
            columns=column,
        )

    def _create_unique_sql(self, model, fields, name=None, condition=None):
        table = self.quote_name(model._meta.db_table)
        if name is None:
            name = self._unique_constraint_name(model, fields)
        else:
            name = self.quote_name(name)

        columns = ', '.join([field.column for field in fields])

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
            columns=columns,
        )

    def _pk_constraint_name(self, model, field):
        return self._create_object_name(
            model, [field], type='primary_key', include_namespace=False
        )

    def _fk_constraint_name(self, model, field, **kwargs) -> str:
        return self._create_object_name(
            model, [field], type='foreign_key', include_namespace=False
        )

    def _check_constraint_name(self, model, field, qualifier=''):
        return self._create_object_name(
            model,
            fields=[field],
            type='unique',
            qualifier=qualifier,
            include_namespace=False,
        )

    def _unique_constraint_name(self, model, fields):
        return self._create_object_name(
            model, fields=fields, type='unique', include_namespace=False
        )

    def _get_name_builder(self):
        return getattr(db_settings, 'DEFAULT_NAME_BUILDER_CLASS')()
