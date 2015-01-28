import json
import django
from django import http
from django.db import connection
from django.conf import settings
from django.shortcuts import get_object_or_404 as orig_get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext

from django.core.serializers.json import DjangoJSONEncoder
# Assuming at least python 2.6, in Django < 1.6, the above class is either a
# packaged simplejson subclass if simplejson is installed, or a core json
# subclass. In Django >= 1.6, it is always a core json subclass. The json.dump
# call in this file needs to be the same thing that the above class is.
if django.get_version() < '1.6':
    try:
        import simplejson
        if issubclass(DjangoJSONEncoder, simplejson.JSONEncoder):
            import simplejson as json  # noqa
    except:
        pass


class GEOS_JSONEncoder(DjangoJSONEncoder):
    def default(self, o):
        try:
            return o.json  # Will therefore support all the GEOS objects
        except:
            pass
        return super(GEOS_JSONEncoder, self).default(o)


def render(request, template_name, context=None):
    if context is None:
        context = {}
#    context['base'] = base or 'base.html'
#    context['connection'] = connection
    return render_to_response(
        template_name, context, context_instance=RequestContext(request)
    )




def output_html(request, title, areas, **kwargs):
    kwargs['json_url'] = request.get_full_path().replace('.html', '')
    kwargs['title'] = title
    kwargs['areas'] = areas
    kwargs['indent_areas'] = kwargs.get('indent_areas', False)
    return render(request, 'mapit/data.html', kwargs)


def output_json(out, code=200):
    if code != 200:
        out['code'] = code
    indent = None
    if settings.DEBUG:
        if isinstance(out, dict):
            out['debug_db_queries'] = connection.queries
        indent = 4
    encoder = GEOS_JSONEncoder(ensure_ascii=False, indent=indent)
    content = encoder.iterencode(out)

    types = {
        400: http.HttpResponseBadRequest,
        404: http.HttpResponseNotFound,
        500: http.HttpResponseServerError,
    }
    if django.get_version() >= '1.5':
        response_type = types.get(code, http.StreamingHttpResponse)
    else:
        response_type = types.get(code, http.HttpResponse)
        # Django 1.4 middleware messes up iterable content
        content = list(content)

    response = response_type(content_type='application/json; charset=utf-8')
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'max-age=2419200'  # 4 weeks
    attr = 'streaming_content' if getattr(response, 'streaming', None) else 'content'
    setattr(response, attr, content)
    return response


def get_object_or_404(klass, format='json', *args, **kwargs):
    try:
        return orig_get_object_or_404(klass, *args, **kwargs)
    except http.Http404 as e:
        from mapit.middleware import ViewException
        raise ViewException(format, str(e), 404)


def json_500(request):
    return output_json({'error': "Sorry, something's gone wrong."}, code=500)


def set_timeout(format):
    cursor = connection.cursor()
    timeout = 10000 if format == 'html' else 10000
    cursor.execute('set session statement_timeout=%d' % timeout)
