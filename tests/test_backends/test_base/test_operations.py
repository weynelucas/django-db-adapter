from django.db import ProgrammingError
from django.test import TestCase

from tests.connection import (
    TestDatabaseOperations,
    TestDatabaseOperationsOptionalRange,
    TestDatabaseOperationsWithSqls,
    test_connection,
)


class SqlAutoincTests(TestCase):
    def test_autoinc_sql_without_overwritten_sqls(self):
        ops = TestDatabaseOperations(connection=test_connection)
        autoinc_sql = ops.autoinc_sql('tbl_article', 'article_id')

        self.assertIsNone(autoinc_sql)

    def test_autoinc_sql_with_overwritten_sqls(self):
        ops = TestDatabaseOperationsWithSqls(connection=test_connection)
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
            ops = TestDatabaseOperationsWithSqls(connection=test_connection)
            ops.autoinc_sql('tbl_article', 'active')

    def test_autoinc_sql_for_optional_integer_field_range(self):
        ops = TestDatabaseOperationsOptionalRange(connection=test_connection)
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
