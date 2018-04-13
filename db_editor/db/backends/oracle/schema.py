from django.db.backends.oracle import schema

from ....utils import string
from ....config import settings


class DatabaseSchemaEditor(schema.DatabaseSchemaEditor):
    prefix_type_map = {
        '_fk': 'FOREIGN_KEY',
        '_uniq': 'UNIQUE', 
        'default': 'INDEX', 
    }

    def _get_index_name_prefix(self, suffix=''):
        has_pattern = any(
            suffix.startswith(pattern) 
            for pattern in self.prefix_type_map.keys()
        )
        return settings.PREFIX.get(
            self.prefix_type_map[pattern] 
            if has_pattern
            else self.prefix_type_map['default']
        )

    def _normalize_index_name(self, index_name, suffix=''):
        # Remove table prefix from object
        index_name = string.replace_prefix(
            index_name, 
            settings.PREFIX.get('TABLE'), 
            ''
        )
        # Normalize name (remove default suffix)
        normalized_index_name = string.replace_suffix(
            index_name, suffix, ''
        )
        return normalized_index_name

    def _create_index_name(self, model, column_name, suffix=''):
        index_name = super(DatabaseSchemaEditor, self)._create_index_name(
            model, column_name, suffix
        )
        return self.quote_name('{}{}'.format(
            self._get_index_name_prefix(suffix), 
            self._normalize_index_name(index_name)
        ))