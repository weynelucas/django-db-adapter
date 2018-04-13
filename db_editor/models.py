from django.db.models.signals import class_prepared, pre_init, post_init

from .config import settings


def is_allowed_backend():
    """
    Check if connection is from allowed backend
    """
    from django.db import connection

    if '*' in settings.ALLOWED_BACKENDS:
        return True
    
    backend = connection         \
        .settings_dict['ENGINE'] \
        .split('.')[-1]          \
        .decode()                

    return backend in settings.ALLOWED_BACKENDS


def add_db_table_prefix(sender, **kwargs):
    """
    Add prefix for all configured models 
    """
    if not is_allowed_backend():
        return

    owner = settings.SCHEMA
    prefix = settings.PREFIX.get('TABLE')
    
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


class_prepared.connect(add_db_table_prefix)