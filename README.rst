Django Birdcage
===============

.. image:: https://img.shields.io/pypi/pyversions/django-birdcage.svg
    :target: https://pypi.python.org/pypi/django-birdcage

.. image:: https://img.shields.io/pypi/v/django-birdcage.svg
    :target: https://pypi.python.org/pypi/django-birdcage

.. image:: https://img.shields.io/pypi/status/django-birdcage.svg
    :target: https://pypi.python.org/pypi/django-birdcage

.. image:: https://img.shields.io/pypi/l/django-birdcage.svg
    :target: https://github.com/pybee/django-birdcage/blob/master/LICENSE

.. image:: https://travis-ci.org/zapier/django-birdcage.svg?branch=master
    :target: https://travis-ci.org/zapier/django-birdcage

When deploying large websites, operations teams will sometimes deploy new code across a subset of the entire collection of webservers. This approach is called a "Canary" deployment. Most users will continue to be served using the old code; only those users hitting a "Canary" machine will see the new code.

Large websites will often use a Canary when the perceived risk of an upgrade is high. For example, upgrading the Django version from 1.8 LTS to 1.11 LTS on a complex site will generally be considered a risky upgrade; a Canary will be used to test that the upgrade is working as expected before switching all webservers over to the upgraded codebase.

Unfortunately, while Django has good *backwards* compatibility guarantees, Canary deployments require *forwards* compatibility as well. This is beacuse a user may have one request served on the new codebase, but subsequent updates served from the old codebase. If information (such as security tokens) aren't both backwards *and* forwards compatible between releases, some users will see errors as the move back and forth between old and new codebases.

Birdcage is a project consisting of tools to help you manage Canary upgrades, by provided *forwards* compatible shims for known problems in Django.

What does Birdcage address?
---------------------------

Django 1.10: Salted CSRF tokens
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Django 1.10 `introduced a change to CSRF handling <https://docs.djangoproject.com/en/1.11/releases/1.10/#csrf>`__ to protect against `BREACH <http://breachattack.com/>`__ attacks. Django 1.10+ can interpret Django < 1.10 CSRF tokens; however, if a user is issued a Django 1.10+ CSRF token, it will be rejected as invalid by Django 1.8.

To address this problem, Birdcage provides a version of Django 1.8's CsrfViewMiddleware that can interpret Django 1.10's CSRF tokens.

* In the settings for your Django 1.8 codebase, replace ``django.middleware.csrf.CsrfViewMiddleware`` in your ``MIDDLEWARE`` setting with ``birdcage.v1_11.csrf.CsrfViewMiddleware``.

* In your Django 1.10+ codebase, continue to use the Django CsrfViewMiddleware.

Why is it called Birdcage?
--------------------------

Well you have to put your canaries *somewhere* to keep them safe... :-)
