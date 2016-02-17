# Middleware to catch any sort of error from our views,
# and output it as either HTML or JSON appropriately

from django import http
from django.template.loader import render_to_string
from mapit.shortcuts import output_json


class ViewException(Exception):
    pass


class ViewExceptionMiddleware(object):
    def process_exception(self, request, exception):
        if not isinstance(exception, ViewException):
            return None

        format, message, code = exception.args
        if format == 'html':
            types = {
                400: http.HttpResponseBadRequest,
                404: http.HttpResponseNotFound,
                500: http.HttpResponseServerError,
            }
            response_type = types.get(code, http.HttpResponse)
            return response_type(render_to_string(
                'mapit/%s.html' % code,
                {'error': message},
                request=request
            ))
        return output_json({'error': message}, code=code)
