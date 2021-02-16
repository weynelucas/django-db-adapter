from django.test import TestCase

from tests.connection import TestDatabaseSchemaEditor, test_connection
from tests.models import Article, Author, Post, Square, Tag


class SqlObjectCreationTests(TestCase):
    def setUp(self):
        self.editor = TestDatabaseSchemaEditor(connection=test_connection)

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
        editor = TestDatabaseSchemaEditor(connection=test_connection)

        model = Post
        field = Post._meta.get_field('name')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NVARCHAR2(30) NULL')

    def test_column_sql_for_not_null_field(self):
        editor = TestDatabaseSchemaEditor(connection=test_connection)

        model = Post
        field = Post._meta.get_field('text')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NCLOB')
        self.assertDictContainsSubset(
            {
                'CHECK': [
                    'ALTER TABLE tbl_post '
                    'ADD CONSTRAINT tbl_post_text_nn_check '
                    'CHECK (text IS NOT NULL)'
                ]
            },
            editor.deferred_column_sql,
        )

    def test_column_sql_for_pk_field(self):
        editor = TestDatabaseSchemaEditor(connection=test_connection)

        model = Post
        field = Post._meta.get_field('id')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NUMBER(11)')
        self.assertDictContainsSubset(
            {
                'PRIMARY KEY': [
                    'ALTER TABLE tbl_post '
                    'ADD CONSTRAINT tbl_post_id_pk '
                    'PRIMARY KEY (id)'
                ],
                'CHECK': [
                    'ALTER TABLE tbl_post '
                    'ADD CONSTRAINT tbl_post_id_nn_check '
                    'CHECK (id IS NOT NULL)'
                ],
            },
            editor.deferred_column_sql,
        )

    def test_column_sql_for_fk_field(self):
        editor = TestDatabaseSchemaEditor(connection=test_connection)

        model = Post
        field = Post._meta.get_field('tag')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NUMBER(11) NULL')
        self.assertDictContainsSubset(
            {
                'FOREIGN KEY': [
                    'ALTER TABLE tbl_post '
                    'ADD CONSTRAINT tbl_post_tag_id_fk '
                    'FOREIGN KEY (tag_id) '
                    'REFERENCES tbl_tag (id) DEFERRABLE INITIALLY DEFERRED'
                ],
            },
            editor.deferred_column_sql,
        )

    def test_column_sql_for_unique_field(self):
        editor = TestDatabaseSchemaEditor(connection=test_connection)

        model = Tag
        field = Tag._meta.get_field('name')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NVARCHAR2(100)')
        self.assertDictContainsSubset(
            {
                'UNIQUE': [
                    'ALTER TABLE tbl_tag '
                    'ADD CONSTRAINT tbl_tag_name_uniq '
                    'UNIQUE (name)'
                ],
                'CHECK': [
                    'ALTER TABLE tbl_tag '
                    'ADD CONSTRAINT tbl_tag_name_nn_check '
                    'CHECK (name IS NOT NULL)'
                ],
            },
            editor.deferred_column_sql,
        )

    def test_column_sql_for_db_check_field(self):
        editor = TestDatabaseSchemaEditor(connection=test_connection)

        model = Square
        field = Square._meta.get_field('side')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NUMBER(11) NULL')
        self.assertDictContainsSubset(
            {
                'CHECK': [
                    'ALTER TABLE tbl_square '
                    'ADD CONSTRAINT tbl_square_side_gte_check '
                    'CHECK (side >= 0)'
                ],
            },
            editor.deferred_column_sql,
        )

    def test_column_sql_for_help_text_field(self):
        editor = TestDatabaseSchemaEditor(connection=test_connection)

        model = Tag
        field = Tag._meta.get_field('description')
        sql, _ = editor.column_sql(model, field)

        self.assertEqual(str(sql), 'NCLOB NULL')
        self.assertDictContainsSubset(
            {
                'COMMENT': [
                    'COMMENT ON COLUMN tbl_tag.description '
                    'IS "Optional description for tag"'
                ],
            },
            editor.deferred_column_sql,
        )


class SqlTableTests(TestCase):
    def test_table_sql(self):
        editor = TestDatabaseSchemaEditor(connection=test_connection)

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
                'tag_id NUMBER(11) NULL)'
            ),
        )
        self.assertDictContainsSubset(
            {
                'UNIQUE': [
                    'ALTER TABLE tbl_article '
                    'ADD CONSTRAINT tbl_article_written_by_name_uniq '
                    'UNIQUE (written_by, name)'
                ],
                'INDEX': [
                    'CREATE INDEX tbl_article_tag_id_idx '
                    'ON tbl_article (tag_id)'
                ],
            },
            editor.deferred_table_sql,
        )

    def test_create_model(self):
        with TestDatabaseSchemaEditor(
            connection=test_connection, collect_sql=True
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
                    'tag_id NUMBER(11) NULL);'
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
                    'ADD CONSTRAINT tbl_article_tag_id_fk '
                    'FOREIGN KEY (tag_id) '
                    'REFERENCES tbl_tag (id) DEFERRABLE INITIALLY DEFERRED;'
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
                (
                    'CREATE INDEX tbl_article_tag_id_idx '
                    'ON tbl_article (tag_id);'
                ),
                # Comments
                (
                    'COMMENT ON COLUMN tbl_article.text '
                    'IS "Article description";'
                ),
            ],
        )
