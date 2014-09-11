import re

from .view_error import *

class JSONPMiddleware(object):
    def process_response(self, request, response):
        # If the response is a redirect, the callback will be dealt
        # on the next request:
        if response.status_code == 302:
            return response
        else:
            cb = request.GET.get('callback')
            if cb and re.match('[a-zA-Z0-9_$.]+$', cb):
                cb = cb.encode('utf-8')
                response.content = b'typeof ' + cb + b" === 'function' && " + cb + b'(' + response.content + b')'
                response.status_code = 200 # Must return OK for JSONP to be processed
            return response

