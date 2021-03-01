from unittest.mock import patch

from django.test import TestCase

from db_adapter.models import transform_db_table
from db_adapter.settings import DatabaseAdapterSettings

from .models import Circle

enable_settings = DatabaseAdapterSettings(
    dict(DEFAULT_DB_TABLE_PATTERN='tbl_{table_name}')
)
disable_settings = DatabaseAdapterSettings(
    dict(
        ENABLE_TRANSFORM_DB_TABLE=False,
        DEFAULT_DB_TABLE_PATTERN='tbl_{table_name}',
    )
)
noformat_settings = DatabaseAdapterSettings()


class TransformDbTableTests(TestCase):
    def tearDown(self):
        Circle._meta.db_table = 'circle'

    @patch('db_adapter.settings.db_settings', enable_settings)
    def test_simple_transform(self):
        transform_db_table(Circle)

        self.assertEqual(Circle._meta.db_table, 'tbl_circle')

    @patch('db_adapter.settings.db_settings', disable_settings)
    def test_transform_with_disable_settings(self):
        transform_db_table(Circle)

        self.assertEqual(Circle._meta.db_table, 'circle')

    @patch('db_adapter.settings.db_settings', noformat_settings)
    def test_transform_without_table_name_pattern(self):
        transform_db_table(Circle)

        self.assertEqual(Circle._meta.db_table, 'circle')
