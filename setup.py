#!/usr/bin/env python
import io
import re
from setuptools import setup, find_packages


with io.open('./birdcage/__init__.py', encoding='utf8') as version_file:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")


with io.open('README.rst', encoding='utf8') as readme:
    long_description = readme.read()


setup(
    name='django-birdcage',
    version=version,
    description='Utilities for maintaining forwards compatibility with Django releases.',
    long_description=long_description,
    author='Russell Keith-Magee',
    author_email='russell.keith-magee@zapier.com',
    url='http://github.com/zapier/django-birdcage',
    keywords=['birdcage', 'Django', 'compatibility'],
    packages=find_packages(exclude=['tests']),
    install_requires=[],
    license='New BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    test_suite='tests'
)
