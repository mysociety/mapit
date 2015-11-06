import itertools
import re

from django.utils import six

from .view_error import ViewException, ViewExceptionMiddleware  # noqa


class JSONPMiddleware(object):
    def process_response(self, request, response):
        # If the response is a redirect, the callback will be dealt with on the next request
        if response.status_code == 302:
            return response

        # If it's not a JSON response, bit silly to add a callback
        if 'application/json' not in response['Content-Type']:
            return response

        # If a callback is already present (fetched from cache)
        if getattr(response, 'content', '')[:7] == 'typeof ':
            return response

        cb = request.GET.get('callback')

        # Callback variable not present or not in the right format
        if not cb or not re.match('[a-zA-Z0-9_$.]+$', cb):
            return response

        cb = cb.encode('utf-8')
        attr = 'streaming_content' if getattr(response, 'streaming', None) else 'content'
        callback_header = b'typeof ' + cb + b" === 'function' && " + cb + b'('
        callback_footer = b')'
        content = getattr(response, attr)
        if not hasattr(content, '__iter__') or isinstance(content, (bytes, six.string_types)):
            content = [content]
        setattr(response, attr, itertools.chain((callback_header,), content, (callback_footer,)))
        response.status_code = 200  # Must return OK for JSONP to be processed
        return response
