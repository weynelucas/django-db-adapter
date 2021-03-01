import json
from unittest.mock import patch

from django.db.backends.base.schema import BaseDatabaseSchemaEditor
from django.test import TestCase

from tests.connection import (
    TestDatabaseSchemaEditor,
    test_connection,
    test_control_connection,
    test_format_connetion,
)
from tests.models import Article, Author, Post, Square, Tag


def enforce_str_values(data: dict) -> dict:
    return json.loads(
        json.dumps(dict(data), default=str),
    )


class SqlObjectCreationTests(TestCase):
    def setUp(self):
        self.editor = TestDatabaseSchemaEditor(test_connection)

    def test_create_primary_key_sql(self):
        model = Author
        field = Author._meta.get_field('id')
        sql = self.editor._create_primary_key_sql(model, field)

        self.assertEqual(
            str(sql),
            (
                'ALTER TABLE tbl_author '
                'ADD CONSTRAINT tbl_author_id_pk '
                'PRIMARY KEY (id)'
            ),
        )

    def test_create_fk_sql(self):
        model = Post
        field = Post._meta.get_field('author')
        sql = self.editor._create_fk_sql(
            model, field, suffix='_fk_%(to_table)s_%(to_column)s'
        )

        self.assertEqual(
            str(sql),
            (
                'ALTER TABLE tbl_post '
                'ADD CONSTRAINT tbl_post_written_by_fk '
                'FOREIGN KEY (written_by) '
                'REFERENCES tbl_author (id) DEFERRABLE INITIALLY DEFERRED'
            ),
        )

    def test_create_unique_sql(self):
        model = Tag
        field = Tag._meta.get_field('name')
        sql = self.editor._create_unique_sql(model, [field.column])

        self.assertEqual(
            str(sql),
            (
                'ALTER TABLE tbl_tag '
                'ADD CONSTRAINT tbl_tag_name_uniq '
                'UNIQUE (name)'
            ),
        )

    def test_create_index_sql(self):
        model = Post
        field = Post._meta.get_field('author')
        sql = self.editor._create_index_sql(model, [field], suffix='_idx')

        self.assertEqual(
            str(sql),
            (
                'CREATE INDEX tbl_post_written_by_idx '
                'ON tbl_post (written_by)'
            ),
        )


class SqlColumnTests(TestCase):
    def test_column_sql_for_null_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        model = Post
        field = Post._meta.get_field('name')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NVARCHAR2(30) NULL')

    def test_column_sql_for_not_null_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        model = Post
        field = Post._meta.get_field('text')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NCLOB')

        column_sql = enforce_str_values(editor.deferred_column_sql)
        self.assertEqual(
            column_sql['CHECK'],
            [
                'ALTER TABLE tbl_post '
                'ADD CONSTRAINT tbl_post_text_nn_check '
                'CHECK (text IS NOT NULL)'
            ],
        )

    def test_column_sql_for_pk_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        model = Tag
        field = Tag._meta.get_field('name')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NVARCHAR2(100)')

        column_sql = enforce_str_values(editor.deferred_column_sql)
        self.assertEqual(
            column_sql['PRIMARY_KEY'],
            [
                'ALTER TABLE tbl_tag '
                'ADD CONSTRAINT tbl_tag_name_pk '
                'PRIMARY KEY (name)'
            ],
        )
        self.assertEqual(
            column_sql['CHECK'],
            [
                'ALTER TABLE tbl_tag '
                'ADD CONSTRAINT tbl_tag_name_nn_check '
                'CHECK (name IS NOT NULL)'
            ],
        )

    def test_column_sql_for_fk_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        model = Post
        field = Post._meta.get_field('tag')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NVARCHAR2(100) NULL')

        column_sql = enforce_str_values(editor.deferred_column_sql)
        self.assertEqual(
            column_sql['FOREIGN_KEY'],
            [
                'ALTER TABLE tbl_post '
                'ADD CONSTRAINT tbl_post_tag_fk '
                'FOREIGN KEY (tag) '
                'REFERENCES tbl_tag (name) DEFERRABLE INITIALLY DEFERRED'
            ],
        )

    def test_column_sql_for_unique_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        model = Tag
        field = Tag._meta.get_field('flag')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NVARCHAR2(30) NULL')

        column_sql = enforce_str_values(editor.deferred_column_sql)
        self.assertEqual(
            column_sql['UNIQUE'],
            [
                'ALTER TABLE tbl_tag '
                'ADD CONSTRAINT tbl_tag_flag_uniq '
                'UNIQUE (flag)'
            ],
        )

    def test_column_sql_for_db_check_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        model = Square
        field = Square._meta.get_field('side')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NUMBER(11) NULL')

        column_sql = enforce_str_values(editor.deferred_column_sql)
        self.assertEqual(
            column_sql['CHECK'],
            [
                'ALTER TABLE tbl_square '
                'ADD CONSTRAINT tbl_square_side_gte_check '
                'CHECK (side >= 0)'
            ],
        )

    def test_column_sql_for_help_text_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        model = Tag
        field = Tag._meta.get_field('description')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NCLOB NULL')

        column_sql = enforce_str_values(editor.deferred_column_sql)
        self.assertEqual(
            column_sql['COMMENT'],
            [
                'COMMENT ON COLUMN tbl_tag.description '
                "IS 'Optional description for tag'"
            ],
        )

    def test_column_sql_for_auto_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)
        model = Article
        field = Article._meta.get_field('article_id')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NUMBER(19)')

        column_sql = enforce_str_values(editor.deferred_column_sql)

        self.assertEqual(
            column_sql['AUTOINCREMENT'],
            [
                '''
CREATE SEQUENCE tbl_article_sq
MINVALUE 1
MAXVALUE 9999999999999999999
START WITH 1
INCREMENT BY 1
CACHE 20\
''',
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
            ],
        )

    def test_column_sql_for_non_column_field(self):
        editor = TestDatabaseSchemaEditor(test_connection)
        model = Article
        field = Article._meta.get_field('liked_by')
        sql, params = editor.column_sql(model, field)

        self.assertIsNone(sql)
        self.assertIsNone(params)


class SqlTableTests(TestCase):
    def test_table_sql(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        sql, _ = editor.table_sql(Article)
        self.assertEqual(
            str(sql),
            (
                'CREATE TABLE tbl_article ('
                'article_id NUMBER(19), '
                'name NVARCHAR2(30), '
                'text NCLOB NULL, '
                'active NUMBER(1) NULL, '
                'written_by NUMBER(11) NULL, '
                'tag NVARCHAR2(100) NULL)'
            ),
        )
        table_sql = enforce_str_values(editor.deferred_table_sql)
        self.assertEqual(
            table_sql['UNIQUE'],
            [
                'ALTER TABLE tbl_article '
                'ADD CONSTRAINT tbl_article_written_by_name_uniq '
                'UNIQUE (written_by, name)'
            ],
        )
        self.assertEqual(
            table_sql['INDEX'],
            [
                'CREATE INDEX tbl_article_tag_idx ON tbl_article (tag)',
            ],
        )

    def test_table_sql_with_grant(self):
        editor = TestDatabaseSchemaEditor(test_control_connection)

        editor.table_sql(Post)
        table_sql = enforce_str_values(editor.deferred_table_sql)
        self.assertEqual(
            table_sql['CONTROL'],
            ['GRANT SELECT, INSERT, UPDATE, DELETE ON tbl_post TO rl_tests'],
        )

    def test_table_sql_without_grant(self):
        editor = TestDatabaseSchemaEditor(test_connection)

        editor.table_sql(Post)
        table_sql = enforce_str_values(editor.deferred_table_sql)
        self.assertEqual(table_sql['CONTROL'], [])

    def test_create_model(self):
        with TestDatabaseSchemaEditor(
            test_connection, collect_sql=True
        ) as editor:
            editor.create_model(Article)

        self.assertEqual(
            editor.collected_sql,
            [
                # Create table
                (
                    'CREATE TABLE tbl_article ('
                    'article_id NUMBER(19), '
                    'name NVARCHAR2(30), '
                    'text NCLOB NULL, '
                    'active NUMBER(1) NULL, '
                    'written_by NUMBER(11) NULL, '
                    'tag NVARCHAR2(100) NULL);'
                ),
                # Primary, unique and foreign keys
                (
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_article_id_pk '
                    'PRIMARY KEY (article_id);'
                ),
                (
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_written_by_name_uniq '
                    'UNIQUE (written_by, name);'
                ),
                (
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_written_by_fk '
                    'FOREIGN KEY (written_by) '
                    'REFERENCES tbl_author (id) '
                    'DEFERRABLE INITIALLY DEFERRED;'
                ),
                (
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_tag_fk '
                    'FOREIGN KEY (tag) '
                    'REFERENCES tbl_tag (name) DEFERRABLE INITIALLY DEFERRED;'
                ),
                # Check constraints
                (
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_article_id_nn_check '
                    'CHECK (article_id IS NOT NULL);'
                ),
                (
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_name_nn_check '
                    'CHECK (name IS NOT NULL);'
                ),
                (
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_active_bool_check '
                    'CHECK (active IN (0,1));'
                ),
                # Indexes
                ('CREATE INDEX tbl_article_tag_idx ' 'ON tbl_article (tag);'),
                # Comments
                (
                    'COMMENT ON COLUMN tbl_article.text '
                    "IS 'Article description';"
                ),
                # Autoincrement SQL
                '''
CREATE SEQUENCE tbl_article_sq
MINVALUE 1
MAXVALUE 9999999999999999999
START WITH 1
INCREMENT BY 1
CACHE 20;\
''',
                '''
CREATE OR REPLACE TRIGGER "tbl_article_tr"
BEFORE INSERT ON tbl_article
FOR EACH ROW
WHEN (new.article_id IS NULL)
    BEGIN
        SELECT "tbl_article_sq".nextval
        INTO :new.article_id FROM dual;
    END;\
''',
            ],
        )

    def test_create_model_with_grant(self):
        with TestDatabaseSchemaEditor(
            test_control_connection, collect_sql=True
        ) as editor:
            editor.create_model(Article)

        self.assertEqual(len(editor.collected_sql), 14)

        *_, grant_table_sql, _, grant_sequence_sql, _ = editor.collected_sql
        self.assertEqual(
            grant_table_sql,
            'GRANT SELECT, INSERT, UPDATE, DELETE ON tbl_article TO rl_tests;',
        )
        self.assertEqual(
            grant_sequence_sql,
            'GRANT SELECT ON tbl_article_sq TO rl_tests;',
        )


class BaseSchemaEditorTests(TestCase):
    @patch.object(BaseDatabaseSchemaEditor, 'execute', retrun_value=None)
    def test_super_execute_called_with_formatted_sql(self, mocked_execute):
        editor = TestDatabaseSchemaEditor(
            test_format_connetion, collect_sql=False
        )
        sql = 'create table "tbl_person" ("name" nvarchar(255))'
        editor.execute(sql, params=())

        formatted_sql = 'CREATE TABLE TBL_PERSON (NAME NVARCHAR(255))'
        mocked_execute.assert_called_once_with(formatted_sql, ())
