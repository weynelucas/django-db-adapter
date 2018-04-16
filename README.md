# django-db-editor
A configurable database backend for Oracle

## Requirements
django-db-editor was tested with the following:

- Python (3+)
- Django (1.11)

The following packages are optional:
- progressbar2 (3.34.0+) - Used only to display progress on `sqlmigrateall` command

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

Any global settings for a Django DB Editor are kept in a single configuration dictionary named `DB_EDITOR`