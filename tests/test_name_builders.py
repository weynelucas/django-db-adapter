from django.test import TestCase

from db_adapter.name_builders import ObjectNameBuilder
from db_adapter.settings import DatabaseAdapterSettings

from .models import Post, Reporter


class ObjectNameBuilderTests(TestCase):
    def setUp(self):
        settings = DatabaseAdapterSettings(
            {
                'DEFAULT_DB_TABLE_FORMAT': 'tbl_{table_name}',
                'DEFAULT_SEQUENCE_NAME': '{table}_seq',
                'DEFAULT_TRIGGER_NAME': 'tg_{table_name}_b',
                'DEFAULT_INDEX_NAME': '{columns}_idx',
                'DEFAULT_PRIMARY_KEY_NAME': 'pk_{name}',
                'DEFAULT_CHECK_NAME': 'check{qualifier}',
                'DEFAULT_UNIQUE_NAME': 'ct_{table_name}_{columns}_uniq',
            }
        )

        self.builder = ObjectNameBuilder(settings=settings)
        self.model = Post
        self.id_field = Post._meta.get_field('id')
        self.tag_field = Post._meta.get_field('tag')
        self.author_field = Post._meta.get_field('author')

    def test_process_table_argument(self):
        """
        The object name should include the entire table name
        """
        obj_name = self.builder.process_name(
            self.model, [self.id_field], type='sequence'
        )
        self.assertEqual(obj_name, 'tbl_post_seq')

    def test_process_table_name_argument(self):

        obj_name = self.builder.process_name(
            self.model, [self.id_field], type='trigger'
        )
        self.assertEqual(obj_name, 'tg_post_b')

    def test_process_columns_argument(self):
        """
        The object name should include the name of all database columns provided
        on call, separated by `_` char
        """
        obj_name = self.builder.process_name(
            self.model, [self.tag_field, self.author_field], type='index'
        )
        self.assertEqual(obj_name, 'tag_id_written_by_idx')

    def test_process_name_argument(self):
        """
        The object name should include the combination of `table_name` and
        `columns` arguments, separated by `_` char.

        If `columns` was not provided, the `_` char should be removed.
        """
        obj_name_with_columns = self.builder.process_name(
            self.model, [self.id_field], type='primary_key'
        )
        obj_name_without_columns = self.builder.process_name(
            self.model, [], type='primary_key'
        )
        self.assertEqual(obj_name_with_columns, 'pk_post_id')
        self.assertEqual(obj_name_without_columns, 'pk_post')

    def test_process_qualifier_argument(self):
        """
        The object name should include the qualifier provided on call, can be an
        extra prefix or suffix
        """
        obj_name = self.builder.process_name(
            self.model, [self.author_field], type='check', qualifier='_nn'
        )
        self.assertEqual(obj_name, 'check_nn')

    def test_process_namespaced_table(self):
        """
        When a model include namespace inside `Meta.db_table`, all object names
        builded from that model should include the namespace too, excluding
        calls with `include_namespace=False`
        """
        kwargs = dict(model=Reporter, fields=[], type='trigger')

        with_namespace = self.builder.process_name(**kwargs)
        without_namespace = self.builder.process_name(
            **kwargs, include_namespace=False
        )

        self.assertEqual(with_namespace, '"tests"."tg_reporter_b"')
        self.assertEqual(without_namespace, 'tg_reporter_b')
