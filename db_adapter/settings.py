"""
Settings are all namespaced in the DB_ADAPTER setting.
For example your project's `settings.py` file might look like this:

DB_ADAPTER = {
    'DEFAULT_TABLE_NAMESPACE': 'db_adapter',
    'DEFAULT_TABLE_IDENTIFIER': 'tb_',
    'ALLOWED_TABLE_IDENTIFIERS': [
        'au_',
        'tb_',
        'tt_',
        'tm_',
        'vw_',
    ],
    'DEFAULT_SEQUENCE_NAME': 'sq_%(table)s',
    'DEFAULT_TRIGGER_NAME': 'tg_%(table_name)s_b',
}

Based on similar settings structure from django-rest-framework:
https://github.com/encode/django-rest-framework/blob/master/rest_framework/settings.py
"""
from django.conf import settings
from django.test.signals import setting_changed

# fmt: off
DEFAULTS = {
    # Table naming patterns
    'DEFAULT_TABLE_IDENTIFIER': '',
    'DEFAULT_TABLE_NAMESPACE': '',
    'ALLOWED_TABLE_IDENTIFIERS': [],

    # Other objects naming pattern
    'DEFAULT_SEQUENCE_NAME': '%(table)s_sq',
    'DEFAULT_TRIGGER_NAME': '%(table)s_%(columns)s_tr',
    'DEFAULT_INDEX_NAME': '%(table)s_%(columns)s_idx',
    'DEFAULT_PRIMARY_KEY_NAME': '%(table)s_%(columns)s_pk',
    'DEFAULT_FOREIGN_KEY_NAME': '%(table)s_%(columns)s_fk',
    'DEFAULT_UNIQUE_NAME': '%(table)s_%(columns)s_uniq',
    'DEFAULT_CHECK_NAME': '%(table)s_%(columns)s%(term)s_check',
}
# fmt: on


class DatabaseAdapterSettings:
    def __init__(self, user_settings=None, defaults=None):
        if user_settings:
            self._user_settings = user_settings

        self.defaults = defaults or DEFAULTS
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
    if setting == 'REST_FRAMEWORK':
        db_settings.reload()


setting_changed.connect(reload_db_settings)
