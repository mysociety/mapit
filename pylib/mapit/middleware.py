import re

class JSONPMiddleware(object):
    def process_response(self, request, response):
        if request.GET.get('callback') and re.match('[a-zA-Z0-9_]+$', request.GET.get('callback')):
            response.content = request.GET.get('callback') + '(' + response.content + ')'
        return response

