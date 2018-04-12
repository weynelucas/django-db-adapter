import pprint

from django.conf import settings
from django.db.backends.oracle import schema

from .utils import without_prefix, get_owner_prefix
from ....utils import string, db_options


class DatabaseSchemaEditor(schema.DatabaseSchemaEditor):
    prefix_type_map = {
        '_fk': 'FOREIGN_KEY',
        '_uniq': 'UNIQUE', 
        'default': 'INDEX', 
    }

    def _get_index_name_prefix(self, suffix=''):
        for pattern in self.prefix_type_map.keys():
            if suffix.startswith(pattern):
                return db_options.get_prefix(self.prefix_type_map[pattern])
        return db_options.get_prefix(self.prefix_type_map['default'])

    def _normalize_index_name(self, index_name, suffix=''):
        index_name = without_prefix(index_name)
        normalized_index_name = string.replace_suffix(index_name, suffix, '')
        normalized_index_name = string.replace_prefix(normalized_index_name, db_options.get_prefix('table'), '')
        return normalized_index_name

    def _create_index_name(self, model, column_name, suffix=''):
        index_name = super(DatabaseSchemaEditor, self)._create_index_name(model, column_name, suffix)
        return self.quote_name('{0}{1}{2}'.format(
            get_owner_prefix(),
            self._get_index_name_prefix(suffix), 
            self._normalize_index_name(index_name)
        ))