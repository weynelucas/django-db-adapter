from django.conf import settings

# Database editor options
DB_EDITOR = getattr(settings, 'DB_EDITOR', {})
# Schema (database owner)
SCHEMA = DB_EDITOR.get('SCHEMA', None)

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
    **DB_EDITOR.get('PREFIX', {}),
}