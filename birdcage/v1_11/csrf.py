"""
Forward compatible Cross Site Request Forgery Middleware.

This module provides a middleware that implements protection
against request forgeries from other sites.

It is required to allow Django deployments < 1.10 to accept
tokens issued on Django 1.10+. This may occur if you have
partial or staged rollouts of a new codebase that includes
an upgrade of Django.
"""
from __future__ import unicode_literals

import re
import string

from django.conf import settings
from django.utils.crypto import constant_time_compare
from django.utils.encoding import force_text
from django.middleware.csrf import (
    _get_new_csrf_key, same_origin, constant_time_compare,
    CsrfViewMiddleware as BaseCsrfViewMiddleware
)
from django.utils.six.moves import zip

REASON_NO_REFERER = "Referer checking failed - no Referer."
REASON_BAD_REFERER = "Referer checking failed - %s does not match %s."
REASON_NO_CSRF_COOKIE = "CSRF cookie not set."
REASON_BAD_TOKEN = "CSRF token missing or incorrect."

CSRF_SECRET_LENGTH = 32
CSRF_TOKEN_LENGTH = 2 * CSRF_SECRET_LENGTH
CSRF_ALLOWED_CHARS = string.ascii_letters + string.digits


def _unsalt_cipher_token(token):
    """
    Given a token (assumed to be a string of CSRF_ALLOWED_CHARS, of length
    CSRF_TOKEN_LENGTH, and that its first half is a salt), use it to decrypt
    the second half to produce the original secret.
    """
    salt = token[:CSRF_SECRET_LENGTH]
    token = token[CSRF_SECRET_LENGTH:]
    chars = CSRF_ALLOWED_CHARS
    pairs = zip((chars.index(x) for x in token), (chars.index(x) for x in salt))
    secret = ''.join(chars[x - y] for x, y in pairs)  # Note negative values are ok
    return secret


def _sanitize_token(token):
    # Allow only ASCII alphanumerics
    if re.search('[^a-zA-Z0-9]', force_text(token)):
        return _get_new_csrf_key()
    elif len(token) == CSRF_TOKEN_LENGTH:
        # Django versions >= 1.10 set cookies to values of CSRF_TOKEN_LENGTH
        # alphanumeric characters. For forwards compatibility, accept
        # such values as salted secrets.
        return _unsalt_cipher_token(token)
    elif len(token) == CSRF_SECRET_LENGTH:
        return token
    return _get_new_csrf_key()


class CsrfViewMiddleware(BaseCsrfViewMiddleware):
    def process_view(self, request, callback, callback_args, callback_kwargs):

        if getattr(request, 'csrf_processing_done', False):
            return None

        try:
            csrf_token = _sanitize_token(
                request.COOKIES[settings.CSRF_COOKIE_NAME])
            # Use same token next time
            request.META['CSRF_COOKIE'] = csrf_token
        except KeyError:
            csrf_token = None
            # Generate token and store it in the request, so it's
            # available to the view.
            request.META["CSRF_COOKIE"] = _get_new_csrf_key()

        # Wait until request.META["CSRF_COOKIE"] has been manipulated before
        # bailing out, so that get_token still works
        if getattr(callback, 'csrf_exempt', False):
            return None

        # Assume that anything not defined as 'safe' by RFC2616 needs protection
        if request.method not in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            if getattr(request, '_dont_enforce_csrf_checks', False):
                # Mechanism to turn off CSRF checks for test suite.
                # It comes after the creation of CSRF cookies, so that
                # everything else continues to work exactly the same
                # (e.g. cookies are sent, etc.), but before any
                # branches that call reject().
                return self._accept(request)

            if request.is_secure():
                # Suppose user visits http://example.com/
                # An active network attacker (man-in-the-middle, MITM) sends a
                # POST form that targets https://example.com/detonate-bomb/ and
                # submits it via JavaScript.
                #
                # The attacker will need to provide a CSRF cookie and token, but
                # that's no problem for a MITM and the session-independent
                # nonce we're using. So the MITM can circumvent the CSRF
                # protection. This is true for any HTTP connection, but anyone
                # using HTTPS expects better! For this reason, for
                # https://example.com/ we need additional protection that treats
                # http://example.com/ as completely untrusted. Under HTTPS,
                # Barth et al. found that the Referer header is missing for
                # same-domain requests in only about 0.2% of cases or less, so
                # we can use strict Referer checking.
                referer = force_text(
                    request.META.get('HTTP_REFERER'),
                    strings_only=True,
                    errors='replace',
                )
                if referer is None:
                    return self._reject(request, REASON_NO_REFERER)

                # Note that request.get_host() includes the port.
                good_referer = 'https://%s/' % request.get_host()
                if not same_origin(referer, good_referer):
                    reason = REASON_BAD_REFERER % (referer, good_referer)
                    return self._reject(request, reason)

            if csrf_token is None:
                # No CSRF cookie. For POST requests, we insist on a CSRF cookie,
                # and in this way we can avoid all CSRF attacks, including login
                # CSRF.
                return self._reject(request, REASON_NO_CSRF_COOKIE)

            # Check non-cookie token for match.
            request_csrf_token = ""
            if request.method == "POST":
                try:
                    request_csrf_token = request.POST.get('csrfmiddlewaretoken', '')
                except IOError:
                    # Handle a broken connection before we've completed reading
                    # the POST data. process_view shouldn't raise any
                    # exceptions, so we'll ignore and serve the user a 403
                    # (assuming they're still listening, which they probably
                    # aren't because of the error).
                    pass

            if request_csrf_token == "":
                # Fall back to X-CSRFToken, to make things easier for AJAX,
                # and possible for PUT/DELETE.
                request_csrf_token = request.META.get('HTTP_X_CSRFTOKEN', '')

            request_csrf_token = _sanitize_token(request_csrf_token)
            if not constant_time_compare(request_csrf_token, csrf_token):
                return self._reject(request, REASON_BAD_TOKEN)

        return self._accept(request)
