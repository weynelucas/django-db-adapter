import re
from typing import Tuple

from django.db.backends.utils import split_identifier

from .settings import db_settings

DEFAULT_TABLE_PATTERN = r'^(?P<prefix>(%(identifiers)s)?)(?P<name>\w+)'


def split_table_identifiers(
    table,
    pattern=DEFAULT_TABLE_PATTERN,
    allowed_identifiers=db_settings.ALLOWED_TABLE_IDENTIFIERS,
) -> Tuple[str, str, str, str]:
    groupdict = {}
    namespace, object = split_identifier(table)

    groupdict.update({'namespace': namespace, 'object': object})

    regex = pattern % dict(identifiers='|'.join(allowed_identifiers))
    match = re.match(regex, object)
    if match:
        groupdict.update(match.groupdict())

    return tuple(groupdict.values())
