import re
from django.utils import simplejson
from django import http
from django.db import connection
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import get_object_or_404 as orig_get_object_or_404
from django.shortcuts import render_to_response
from django.template.loader import render_to_string
from django.template import RequestContext

class GEOS_JSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return o.json # Will therefore support all the GEOS objects
        except:
            pass
        return super(GEOS_JSONEncoder, self).default(o)

def render(request, template_name, context=None):
    if context is None: context = {}
#    context['base'] = base or 'base.html'
#    context['connection'] = connection
    return render_to_response(
        template_name, context, context_instance = RequestContext(request)
    )

def output_html(request, title, areas, **kwargs):
    kwargs['json_url'] = request.path.replace('.html', '')
    kwargs['title'] = title
    kwargs['areas'] = areas
    return render(request, 'data.html', kwargs)

def output_error(format, message, code):
    if format=='html':
        types = {
            400: http.HttpResponseBadRequest,
            404: http.HttpResponseNotFound,
            500: http.HttpResponseServerError,
        }
        response_type = types.get(code, http.HttpResponse)
        return response_type(render_to_string('%s.html' % code, {
            'error': message,
        }))
    return output_json({ 'error': message }, code=code)

def output_json(out, code=200):
    types = {
        400: http.HttpResponseBadRequest,
        404: http.HttpResponseNotFound,
        500: http.HttpResponseServerError,
    }
    response_type = types.get(code, http.HttpResponse)
    response = response_type(content_type='application/json; charset=utf-8')
    response['Access-Control-Allow-Origin'] = '*'
    if code != 200:
        out['code'] = code
    indent = None
    if settings.DEBUG:
        if isinstance(out, dict):
            out['debug_db_queries'] = connection.queries
        indent = 4
    simplejson.dump(out, response, ensure_ascii=False, cls=GEOS_JSONEncoder, indent=indent)
    return response

def get_object_or_404(klass, format='json', *args, **kwargs):
    try:
        return orig_get_object_or_404(klass, *args, **kwargs)
    except http.Http404, e:
        return output_error(format, str(e), 404)

def json_500(request):
    return output_json({ 'error': "Sorry, something's gone wrong." }, code=500)

def set_timeout(format):
    cursor = connection.cursor()
    timeout = 10000 if format == 'html' else 10000
    cursor.execute('set session statement_timeout=%d' % timeout)

