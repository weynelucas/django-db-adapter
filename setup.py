"""
A setuptools for django-db-adapter
"""
from setuptools import setup, find_packages
from codecs import open


with open('README.md') as f:
    long_description = f.read()


setup(
    name='django-db-adapter', 
    version='1.0.1', 
    description='A configurable database backend for Oracle',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/weynelucas/django-db-adapter/', 
    download_url="https://github.com/weynelucas/django-db-adapter/archive/1.0.1.tar.gz",
    author='Lucas Weyne',
    author_email='weynelucas@gmail.com',
    classifiers=[ 
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Topic :: Internet :: WWW/HTTP',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
    keywords='django database schema editor oracle django-db-adapter',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
)