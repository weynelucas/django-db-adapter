# Django DB Adapter

[![Build](https://github.com/weynelucas/django-db-adapter/workflows/Build/badge.svg)](https://github.com/weynelucas/django-db-adapter/actions)
[![codecov](https://codecov.io/gh/weynelucas/django-db-adapter/branch/develop/graph/badge.svg?token=EZyTLmsPhm)](https://codecov.io/gh/weynelucas/django-db-adapter)
[![PyPI - Release](https://img.shields.io/pypi/v/django-db-adapter.svg)](https://pypi.python.org/pypi/django-db-adapter)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/django-db-adapter)](https://pypi.python.org/pypi/django-db-adapter)
[![PyPI - Django Version](https://img.shields.io/pypi/djversions/django-db-adapters)](https://pypi.python.org/pypi/django-db-adapter)


A configurable database backend to customize schema creation

# Requirements
- Python (3.6, 3.7, 3.8, 3.9)
- Django (1.11, 2.2)


We highly recommend and only officially support the latest patch release of each Python and Django series.

# Installation
Install using `pip`...

```bash
pip install django-db-adapter
```

Add `'db_adapter'` to your `INSTALLED_APPS` setting.

```python
INSTALLED_APPS = [
    ...
    'db_adapter',
]
```
