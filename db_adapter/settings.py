"""
Settings are all namespaced in the DB_ADAPTER setting.
For example your project's `settings.py` file might look like this:

DB_ADAPTER = {
    'DEFAULT_DB_TABLE_FORMAT': '"pools"."tb_{table_name}"',
    'DEFAULT_SEQUENCE_NAME': 'sq_{table_name}',
    'DEFAULT_TRIGGER_NAME': 'tg_{table_name}_b',
    'DEFAULT_INDEX_NAME': 'ix_{name}',
    'DEFAULT_PRIMARY_KEY_NAME': 'pk_{name}',
    'DEFAULT_FOREIGN_KEY_NAME': 'fk_{name}',
    'DEFAULT_UNIQUE_NAME': 'ct_{name}_uniq',
    'DEFAULT_CHECK_NAME': 'ct_{name}{qualifier}',
}

Based on similar settings structure from django-rest-framework:
https://github.com/encode/django-rest-framework/blob/master/rest_framework/settings.py
"""
from django.conf import settings
from django.test.signals import setting_changed
from django.utils.module_loading import import_string

# fmt: off
DEFAULTS = {
    # Table naming patterns
    'DEFAULT_DB_TABLE_FORMAT': '',
    'IGNORE_DB_TABLE_FORMATS': [],
    'ENABLE_DB_TABLE_NORMALIZATION': True,

    # Other objects naming pattern
    'DEFAULT_SEQUENCE_NAME': '{table}_sq',
    'DEFAULT_TRIGGER_NAME': '{table}_tr',
    'DEFAULT_INDEX_NAME': '{table}_{columns}_idx',
    'DEFAULT_PRIMARY_KEY_NAME': '{table}_{columns}_pk',
    'DEFAULT_FOREIGN_KEY_NAME': '{table}_{columns}_fk',
    'DEFAULT_UNIQUE_NAME': '{table}_{columns}_uniq',
    'DEFAULT_CHECK_NAME': '{table}_{columns}{qualifier}_check',

    # Grant options
    'DEFAULT_ROLE_NAME': '',

    # Base policies
    'DEFAULT_NAME_BUILDER_CLASS': 'db_adapter.name_builders.ObjectNameBuilder',
    'DEFAULT_OBJECT_PRIVILEGES': [
        'SELECT',
        'INSERT',
        'UPDATE',
        'DELETE',
    ],
    'SQL_FORMAT_OPTIONS': {
        'unquote': False,
    },
}
# fmt: on

IMPORT_STRINGS = [
    'DEFAULT_NAME_BUILDER_CLASS',
]

DICT_STRINGS = [
    'SQL_FORMAT_OPTIONS',
]


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import '%s' for DB_ADAPTER setting '%s'. %s: %s." % (
            val,
            setting_name,
            e.__class__.__name__,
            e,
        )
        raise ImportError(msg)


class DatabaseAdapterSettings:
    def __init__(
        self,
        user_settings=None,
        defaults=None,
        import_strings=None,
        dict_strings=None,
    ):
        if user_settings:
            self._user_settings = user_settings

        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self.dict_strings = dict_strings or DICT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, '_user_settings'):
            self._user_settings = getattr(settings, 'DB_ADAPTER', {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid API setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Merge user and default settings
        if attr in self.dict_strings:
            val = {
                **self.defaults[attr],
                **self._user_settings.get(attr, {}),
            }

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, '_user_settings'):
            delattr(self, '_user_settings')


db_settings = DatabaseAdapterSettings(None, DEFAULTS)


def reload_db_settings(*args, **kwargs):
    setting = kwargs['setting']
    if setting == 'DB_ADAPTER':
        db_settings.reload()


setting_changed.connect(reload_db_settings)
