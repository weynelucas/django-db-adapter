from django.test import TestCase

from db_adapter.settings import DEFAULTS, DatabaseAdapterSettings


class DatabaseAdapterSettingsTests(TestCase):
    def test_reload(self):
        setting = 'ENABLE_DB_TABLE_NORMALIZATION'
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

    def test_get_invalid_import_string(self):
        settings = DatabaseAdapterSettings(
            user_settings={
                'DEFAULT_NAME_BUILDER_CLASS': 'module.package.attribute'
            }
        )

        with self.assertRaises(ImportError):
            getattr(settings, 'DEFAULT_NAME_BUILDER_CLASS')

    def test_none_import_string(self):
        settings = DatabaseAdapterSettings(
            user_settings={'DEFAULT_NAME_BUILDER_CLASS': None}
        )

        self.assertIsNone(getattr(settings, 'DEFAULT_NAME_BUILDER_CLASS'))

    def test_invalid_type_import_string(self):
        settings = DatabaseAdapterSettings(
            user_settings={'DEFAULT_NAME_BUILDER_CLASS': True}
        )

        self.assertTrue(getattr(settings, 'DEFAULT_NAME_BUILDER_CLASS'))
