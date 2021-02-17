from unittest.mock import patch

from django.test import TestCase

from db_adapter.models import apply_db_table_normalization
from db_adapter.settings import DatabaseAdapterSettings

from .models import Circle

enable_settings = DatabaseAdapterSettings(
    dict(DEFAULT_DB_TABLE_FORMAT='tbl_{table_name}')
)
disable_settings = DatabaseAdapterSettings(
    dict(
        ENABLE_DB_TABLE_NORMALIZATION=False,
        DEFAULT_DB_TABLE_FORMAT='tbl_{table_name}',
    )
)
noformat_settings = DatabaseAdapterSettings()


class ApplyDbTableNormalizationTests(TestCase):
    def tearDown(self):
        Circle._meta.db_table = 'circle'

    @patch('db_adapter.settings.db_settings', enable_settings)
    def test_normalize(self):
        apply_db_table_normalization(Circle)

        self.assertEqual(Circle._meta.db_table, 'tbl_circle')

    @patch('db_adapter.settings.db_settings', disable_settings)
    def test_normalize_with_disable_settings(self):
        apply_db_table_normalization(Circle)

        self.assertEqual(Circle._meta.db_table, 'circle')

    @patch('db_adapter.settings.db_settings', noformat_settings)
    def test_normalize_without_db_table_format(self):
        apply_db_table_normalization(Circle)

        self.assertEqual(Circle._meta.db_table, 'circle')
