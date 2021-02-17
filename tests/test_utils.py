from django.db import models
from django.test import TestCase

from db_adapter.utils import (
    TableIdentifiers,
    enforce_model_fields,
    normalize_table,
    split_table_identifiers,
)

from .models import Post


class SplitTableIdentifierTests(TestCase):
    def test_split_table_name(self):
        parts = split_table_identifiers('django_migrations')

        self.assertIsInstance(parts, TableIdentifiers)
        self.assertEqual(
            parts,
            ('', 'django_migrations', 'django_migrations'),
        )

    def test_split_table_namespace(self):
        parts = split_table_identifiers(
            '"db_adapter"."auth_user"',
        )

        self.assertEqual(
            parts,
            ('db_adapter', 'auth_user', 'auth_user'),
        )

    def test_split_table_suffix_format(self):
        parts = split_table_identifiers(
            '"db_adapter"."django_session_tbl"',
            format='{table_name}_tbl',
        )

        self.assertEqual(
            parts,
            ('db_adapter', 'django_session_tbl', 'django_session'),
        )

    def test_split_table_namespace_format(self):
        parts = split_table_identifiers(
            'tbl_django_site',
            format='"db_adapter"."tbl_{table_name}"',
        )

        self.assertEqual(
            parts,
            ('', 'tbl_django_site', 'django_site'),
        )


class NormalizeTableTests(TestCase):
    def test_normalize_table_name(self):
        with_prefix = normalize_table('django_site', 'tbl_{table_name}')
        with_suffix = normalize_table('django_site', '{table_name}_tbl')
        with_namespace = normalize_table(
            'django_site', '"db_adapter"."{table_name}"'
        )

        self.assertEqual(with_prefix, 'tbl_django_site')
        self.assertEqual(with_suffix, 'django_site_tbl')
        self.assertEqual(with_namespace, '"db_adapter"."django_site"')

    def test_ignore_already_normalized_table(self):
        with_prefix = normalize_table('tbl_django_site', 'tbl_{table_name}')
        with_suffix = normalize_table('django_site_tbl', '{table_name}_tbl')
        with_namespace = normalize_table(
            '"db_adapter"."django_site"', '"db_adapter"."{table_name}"'
        )

        self.assertEqual(with_prefix, 'tbl_django_site')
        self.assertEqual(with_suffix, 'django_site_tbl')
        self.assertEqual(with_namespace, '"db_adapter"."django_site"')

    def test_add_namespace_from_format_when_not_provided(self):
        without_namespace = normalize_table(
            'tbl_django_site', '"db_adapter"."tbl_{table_name}"'
        )
        self.assertEqual(without_namespace, '"db_adapter"."tbl_django_site"')

    def test_ignore_exclude_formats(self):
        format = '"db_adapter"."tbl_{table_name}"'
        exclude = [
            '"{}"."{}"',
            'adt_{}',
            'django_migrations',
        ]

        excluded_by_namespace = normalize_table(
            '"admin"."django_site"', format, exclude
        )
        excluded_by_prefix = normalize_table('adt_report', format, exclude)
        excluded_by_name = normalize_table('django_migrations', format, exclude)
        included = normalize_table('django_session', format, exclude)

        self.assertEqual(excluded_by_namespace, '"admin"."django_site"')
        self.assertEqual(excluded_by_prefix, 'adt_report')
        self.assertEqual(excluded_by_name, 'django_migrations')
        self.assertEqual(included, '"db_adapter"."tbl_django_session"')


class EnforceModelFieldsTests(TestCase):
    def test_enforce_model_fields(self):
        fields = enforce_model_fields(
            Post,
            [
                Post._meta.get_field('tag'),
                'written_by',
            ],
        )

        self.assertIsInstance(fields, list)
        self.assertTrue(len(fields), 2)
        self.assertTrue(all(isinstance(f, models.Field) for f in fields))

        tag_field, author_field = fields
        self.assertEqual(tag_field.name, 'tag')
        self.assertEqual(tag_field.column, 'tag')
        self.assertEqual(author_field.name, 'author')
        self.assertEqual(author_field.column, 'written_by')
