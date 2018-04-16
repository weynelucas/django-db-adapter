# django-db-editor
A configurable database backend for Oracle

## Requirements
django-db-editor was tested with the following requirements:

- [Python](https://www.python.org/) (3+)
- [Django](https://docs.djangoproject.com/) (1.11)
- [cx_Oracle](http://cx-oracle.readthedocs.io/en/latest/) (5.2+)

The following packages are optional:
- [progressbar2](https://pypi.python.org/pypi/progressbar2) (3.34.0+) - Used only to display progress during `sqlmigrateall` command

## Installation
Install using pip, including any optional packages you want...

```
pip install django-db-editor
```

...or clone the project from github.

```
git clone https://github.com/weynelucas/django-db-editor.git
```

Add `'db_editor'` at the top of your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = (
    ...,
    'db_editor'
)
```

## Quickstart
Any global settings for a django-db-editor are kept in a single configuration dictionary named `DB_EDITOR`

```python
DB_EDITOR = {
    'SCHEMA': 'CONN_ORCL',
    'ALLOWED_BACKENDS': ['oracle'],
    'PREFIX': {
        'TABLE': 'tb_',
        'FOREIGN_KEY': 'ce_',
        'INDEX': 'ix_',
        'UNIQUE': 'ct_',
        'TRIGGER': 'tg_',
        'SEQUENCE': 'sq_'
    }
}
```

You must setting the connection parameter `ENGINE` from `DATABASES` with the custom oracle database backend to apply your `DB_EDITOR` settings.

```python
DATABASES = {
    'default': {
        'ENGINE': 'db_editor.db.backends.oracle',
        'NAME': 'mydatabase',
        'USER': 'mydatabaseuser',
        'PASSWORD': 'mypassword',
        'HOST': '127.0.0.1',
        'PORT': '1521'
    }
}
```

## Settings
Configuration for django-db-editor is all namespaced inside a single Django setting, named `DB_EDITOR`.

If you need to access the values of `db_editor` settings in your project, you should use the `settings` object. For example.

```python
from db_editor.config import settings

print settings.SCHEMA
print settings.PREFIX['TABLE']
```

### Global settings

#### `SCHEMA`
Default: `None`

String with user schema name of you database connection.

#### `ALLOWED_BACKENDS`
Default: `[ '*' ]`

List of database backends names allowed to perform non-oracle actions. Table prefixes and the command `sqlmigrateall` does not require a oracle backend, but is possible. Options are: `'mysql'`, `'oracle'`, `'postgresql'`, `'postgresql_psycopg2'`, `'sqlite'` or `*` for allow all backends


