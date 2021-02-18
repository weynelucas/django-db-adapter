from django.db import ProgrammingError
from django.test import TestCase

from tests.connection import (
    TestDatabaseOperations,
    TestDatabaseOperationsAutoincSql,
    TestDatabaseOperationsControlSql,
    TestDatabaseOperationsOptionalRange,
    test_connection,
    test_control_connection,
)


class SqlControlTests(TestCase):
    def test_control_sql(self):
        ops = TestDatabaseOperationsAutoincSql(test_connection)
        control_ops = TestDatabaseOperationsControlSql(test_control_connection)

        sql_none = ops.control_sql('tbl_article')
        sql_default_privileges = control_ops.control_sql('tbl_article')
        sql_custom_privileges = control_ops.control_sql(
            'tbl_article_sq', privileges=['SELECT']
        )

        self.assertIsNone(sql_none)
        self.assertEqual(
            sql_default_privileges,
            'GRANT SELECT, INSERT, UPDATE, DELETE ON tbl_article TO rl_tests',
        )
        self.assertEqual(
            sql_custom_privileges,
            'GRANT SELECT ON tbl_article_sq TO rl_tests',
        )


class SqlAutoincTests(TestCase):
    def test_autoinc_sql_without_overwritten_sqls(self):
        ops = TestDatabaseOperations(test_connection)
        autoinc_sql = ops.autoinc_sql('tbl_article', 'article_id')

        self.assertIsNone(autoinc_sql)

    def test_autoinc_sql_with_overwritten_sqls(self):
        ops = TestDatabaseOperationsAutoincSql(test_connection)
        autoinc_sql = ops.autoinc_sql('tbl_article', 'article_id')

        self.assertEqual(len(autoinc_sql), 2)

        sequence_sql, trigger_sql = autoinc_sql
        self.assertEqual(
            sequence_sql,
            '''
CREATE SEQUENCE tbl_article_sq
MINVALUE 1
MAXVALUE 9999999999999999999
START WITH 1
INCREMENT BY 1
CACHE 20\
''',
        )

        self.assertEqual(
            trigger_sql,
            '''
CREATE OR REPLACE TRIGGER "tbl_article_tr"
BEFORE INSERT ON tbl_article
FOR EACH ROW
WHEN (new.article_id IS NULL)
    BEGIN
        SELECT "tbl_article_sq".nextval
        INTO :new.article_id FROM dual;
    END\
''',
        )

    def test_autoinc_sql_for_required_integer_field_range(self):
        """
        The internal type of column bound to the field must have a entry on
        `internal_field_tanges` when `sql_create_sequence` declares an
        `sq_max_value` argument
        """
        msg = (
            'Cannot retrieve the range of the column type bound to the field '
            'active'
        )

        with self.assertRaises(ProgrammingError, msg=msg):
            ops = TestDatabaseOperationsAutoincSql(test_connection)
            ops.autoinc_sql('tbl_article', 'active')

    def test_autoinc_sql_for_optional_integer_field_range(self):
        ops = TestDatabaseOperationsOptionalRange(test_connection)
        autoinc_sql = ops.autoinc_sql('tbl_article', 'active')

        self.assertEqual(len(autoinc_sql), 2)

        sequence_sql, _ = autoinc_sql
        self.assertEqual(
            sequence_sql,
            '''
DECLARE
    i INTEGER;
BEGIN
    SELECT COUNT(1) INTO i FROM USER_SEQUENCES
        WHERE SEQUENCE_NAME = 'tbl_article_sq';
    IF i = 0 THEN
        EXECUTE IMMEDIATE 'CREATE SEQUENCE "tbl_article_sq"';
    END IF;
END''',
        )

    def test_autoinc_sql_grant_sequence(self):
        ops = TestDatabaseOperationsControlSql(test_control_connection)
        autoinc_sql = ops.autoinc_sql('tbl_article', 'article_id')

        self.assertEqual(len(autoinc_sql), 3)

        _, grant_sequence_sql, _ = autoinc_sql
        self.assertEqual(
            grant_sequence_sql, 'GRANT SELECT ON tbl_article_sq TO rl_tests'
        )
