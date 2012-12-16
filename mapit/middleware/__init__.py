import re

from view_error import *

class JSONPMiddleware(object):
    def process_response(self, request, response):
        # If the response is a redirect, the callback will be dealt
        # on the next request:
        if response.status_code == 302:
            return response
        else:
            if request.GET.get('callback') and re.match('[a-zA-Z0-9_]+$', request.GET.get('callback')):
                response.content = request.GET.get('callback').encode('utf-8') + '(' + response.content + ')'
                response.status_code = 200 # Must return OK for JSONP to be processed
            return response

