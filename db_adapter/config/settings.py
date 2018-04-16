from django.db import connection
from django.conf import settings


# Database editor options
DB_ADAPTER = getattr(settings, 'DB_ADAPTER', {})

# Schema (database owner)
SCHEMA = DB_ADAPTER.get('SCHEMA', '')

# Accepted backends for non oracle database actions
ALLOWED_BACKENDS = DB_ADAPTER.get('ALLOW_BACKENDS', ['*'])

# Map between object type and prefix
DEFAULT_PREFIX = {
    'TABLE': 'tb_',
    'FOREIGN_KEY': 'fk_',
    'INDEX': 'ix_',
    'UNIQUE': 'uniq_',
    'TRIGGER': 'tg_',
    'SEQUENCE': 'sq_'
}
PREFIX = {
    **DEFAULT_PREFIX,
    **DB_ADAPTER.get('PREFIX', {}),
}