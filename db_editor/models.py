from django.conf import settings
from django.db import connection
from django.db.models.signals import class_prepared, pre_init, post_init

from intmed_framework.utils import db_options


def add_db_prefix(sender, **kwargs):
    if not db_options.is_valid_vendor():
        return

    prefix = db_options.get_prefix('table')
    owner = getattr(settings, 'DB_SCHEMA') or ''
    
    if owner:
        owner = owner + '.'
    
    if isinstance(prefix, dict):
        app_label = sender._meta.app_label.lower()
        sender_name = sender._meta.object_name.lower()
        full_name = app_label + "." + sender_name
        if full_name in prefix:
            prefix = prefix[full_name]
        elif app_label in prefix:
            prefix = prefix[app_label]
        else:
            prefix = prefix.get(None, None)

    if prefix:
        sender._meta.db_table = owner + prefix + sender._meta.db_table


class_prepared.connect(add_db_prefix)