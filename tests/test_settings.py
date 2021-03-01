from unittest.mock import patch

from django.test import TestCase

from db_adapter.settings import (
    DEFAULTS,
    DatabaseAdapterSettings,
    reload_db_settings,
)


class DatabaseAdapterSettingsTests(TestCase):
    def test_reload(self):
        setting = 'ENABLE_TRANSFORM_DB_TABLE'
        value = False

        settings = DatabaseAdapterSettings(user_settings={setting: value})

        self.assertEqual(getattr(settings, setting), value)
        self.assertIn(setting, settings._cached_attrs)
        self.assertIn('_user_settings', settings.__dict__)
        self.assertIn(setting, settings._user_settings)

        settings.reload()

        self.assertNotIn(setting, settings._cached_attrs)
        self.assertNotIn('_user_settings', settings.__dict__)
        self.assertEqual(getattr(settings, setting), DEFAULTS[setting])

    @patch.object(DatabaseAdapterSettings, 'reload', retrun_value=None)
    def test_reload_called_when_setting_changes(self, mocked_reload):
        reload_db_settings(setting='DB_ADAPTER')
        self.assertTrue(mocked_reload.called)

    @patch.object(DatabaseAdapterSettings, 'reload', retrun_value=None)
    def test_reload_not_called_when_setting_not_change(self, mocked_reload):
        reload_db_settings(setting='DATABASES')
        self.assertFalse(mocked_reload.called)

    def test_get_invalid_import_string(self):
        settings = DatabaseAdapterSettings(
            user_settings={'NAME_BUILDER_CLASS': 'module.package.attribute'}
        )

        with self.assertRaises(ImportError):
            getattr(settings, 'NAME_BUILDER_CLASS')

    def test_none_import_string(self):
        settings = DatabaseAdapterSettings(
            user_settings={'NAME_BUILDER_CLASS': None}
        )

        self.assertIsNone(getattr(settings, 'NAME_BUILDER_CLASS'))

    def test_invalid_type_import_string(self):
        settings = DatabaseAdapterSettings(
            user_settings={'NAME_BUILDER_CLASS': True}
        )

        self.assertTrue(getattr(settings, 'NAME_BUILDER_CLASS'))

    def test_dict_settings(self):
        kwargs = dict(
            defaults={'SQL_FORMAT_OPTIONS': {'unquote': False}},
            dict_strings=['SQL_FORMAT_OPTIONS'],
        )

        default_cfg = DatabaseAdapterSettings(**kwargs)
        self.assertFalse(default_cfg.SQL_FORMAT_OPTIONS['unquote'])
        self.assertNotIn('keyword_case', default_cfg.SQL_FORMAT_OPTIONS)

        override_cfg = DatabaseAdapterSettings(
            user_settings={
                'SQL_FORMAT_OPTIONS': {'unquote': True, 'keyword_case': 'upper'}
            },
            **kwargs,
        )
        self.assertTrue(override_cfg.SQL_FORMAT_OPTIONS['unquote'])
        self.assertEqual(
            override_cfg.SQL_FORMAT_OPTIONS.get('keyword_case'), 'upper'
        )
