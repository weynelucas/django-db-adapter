from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.db.backends.dummy.base import (
    DatabaseOperations as DjangoDatabaseOperations,
    DatabaseWrapper,
)
from django.db.utils import DEFAULT_DB_ALIAS

from db_adapter.db.backends.base.operations import DatabaseOperations
from db_adapter.db.backends.base.schema import DatabaseSchemaEditor


class TestDatabaseOperations(DatabaseOperations, DjangoDatabaseOperations):
    def tablespace_sql(self, tablespace, inline=False) -> str:
        return ''

    def deferrable_sql(self) -> str:
        return ' DEFERRABLE INITIALLY DEFERRED'

    def quote_name(self, name: str) -> str:
        return name


class TestDatabaseOperationsWithSqls(TestDatabaseOperations):
    integer_field_ranges = {
        'SmallIntegerField': (-99999999999, 99999999999),
        'IntegerField': (-99999999999, 99999999999),
        'BigIntegerField': (-9999999999999999999, 9999999999999999999),
        'PositiveSmallIntegerField': (0, 99999999999),
        'PositiveIntegerField': (0, 99999999999),
        'SmallAutoField': (-99999, 99999),
        'AutoField': (-99999999999, 99999999999),
        'BigAutoField': (-9999999999999999999, 9999999999999999999),
    }

    sql_create_sequence = '''
CREATE SEQUENCE %(sq_name)s
MINVALUE 1
MAXVALUE %(sq_max_value)s
START WITH 1
INCREMENT BY 1
CACHE 20\
'''
    sql_create_trigger = '''
CREATE OR REPLACE TRIGGER "%(tr_name)s"
BEFORE INSERT ON %(tbl_name)s
FOR EACH ROW
WHEN (new.%(col_name)s IS NULL)
    BEGIN
        SELECT "%(sq_name)s".nextval
        INTO :new.%(col_name)s FROM dual;
    END\
'''


class TestDatabaseOperationsOptionalRange(TestDatabaseOperationsWithSqls):
    sql_create_sequence = '''
DECLARE
    i INTEGER;
BEGIN
    SELECT COUNT(1) INTO i FROM USER_SEQUENCES
        WHERE SEQUENCE_NAME = '%(sq_name)s';
    IF i = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE "%(sq_name)s"';
    END IF;
END\
'''


class TestDatabaseSchemaEditor(DatabaseSchemaEditor, BaseDatabaseSchemaEditor):
    pass


class TestDatabaseWrapper(DatabaseWrapper):
    ops_class = TestDatabaseOperationsWithSqls
    SchemaEditorClass = TestDatabaseSchemaEditor

    data_types = {
        'AutoField': 'NUMBER(11)',
        'BigAutoField': 'NUMBER(19)',
        'BinaryField': 'BLOB',
        'BooleanField': 'NUMBER(1)',
        'NullBooleanField': 'NUMBER(1)',
        'CharField': 'NVARCHAR2(%(max_length)s)',
        'DateField': 'DATE',
        'DateTimeField': 'TIMESTAMP',
        'DecimalField': 'NUMBER(%(max_digits)s, %(decimal_places)s)',
        'DurationField': 'INTERVAL DAY(9) TO SECOND(6)',
        'FileField': 'NVARCHAR2(%(max_length)s)',
        'FilePathField': 'NVARCHAR2(%(max_length)s)',
        'FloatField': 'DOUBLE PRECISION',
        'IntegerField': 'NUMBER(11)',
        'JSONField': 'NCLOB',
        'BigIntegerField': 'NUMBER(19)',
        'IPAddressField': 'VARCHAR2(15)',
        'GenericIPAddressField': 'VARCHAR2(39)',
        'OneToOneField': 'NUMBER(11)',
        'PositiveBigIntegerField': 'NUMBER(19)',
        'PositiveIntegerField': 'NUMBER(11)',
        'PositiveSmallIntegerField': 'NUMBER(11)',
        'SlugField': 'NVARCHAR2(%(max_length)s)',
        'SmallAutoField': 'NUMBER(5)',
        'SmallIntegerField': 'NUMBER(11)',
        'TextField': 'NCLOB',
        'TimeField': 'TIMESTAMP',
        'URLField': 'VARCHAR2(%(max_length)s)',
        'UUIDField': 'VARCHAR2(32)',
    }
    data_type_check_constraints = {
        'BooleanField': '%(qn_column)s IN (0,1)',
        'NullBooleanField': '%(qn_column)s IN (0,1)',
        'PositiveIntegerField': '%(qn_column)s >= 0',
        'PositiveSmallIntegerField': '%(qn_column)s >= 0',
    }
    data_type_check_constraints_suffixes = {
        'BooleanField': '_bool',
        'NullBooleanField': '_bool',
        'PositiveIntegerField': '_gte',
        'PositiveSmallIntegerField': '_gte',
    }


test_connection = TestDatabaseWrapper(settings_dict={}, alias=DEFAULT_DB_ALIAS)
