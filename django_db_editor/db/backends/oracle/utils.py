from django.conf import settings

from ....utils import string, db_options


def get_owner_prefix():
    owner = db_options.get_owner()
    return owner + '.' if owner else owner


def get_full_prefix():
    return get_owner_prefix() + db_options.get_prefix('table')


def without_prefix(table):
    return string.replace_prefix(table, get_full_prefix(), '')