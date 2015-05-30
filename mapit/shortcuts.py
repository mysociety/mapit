import itertools
import json

import django
from django import http
from django.db import connection
from django.conf import settings
from django.shortcuts import get_object_or_404 as orig_get_object_or_404
from django.template import loader
from django.utils.six.moves import map
from django.utils.encoding import smart_bytes
from django.utils.translation import ugettext as _

from mapit.iterables import defaultiter
from mapit.djangopatch import render_to_string

# In 1.8, we no longer need to pass a Context() so stub it out
if django.get_version() < '1.8':
    from django.template import Context
else:
    Context = lambda x: x

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


def output_html(request, title, areas, **kwargs):
    kwargs['json_url'] = request.get_full_path().replace('.html', '')
    kwargs['title'] = title
    tpl = render_to_string('mapit/data.html', kwargs, request=request)
    wraps = tpl.split('!!!DATA!!!')

    indent_areas = kwargs.get('indent_areas', False)
    item_tpl = loader.get_template('mapit/areas_item.html')
    areas = map(lambda area: item_tpl.render(Context({'area': area, 'indent_areas': indent_areas})), areas)
    areas = defaultiter(areas, '<li>' + _('No matching areas found.') + '</li>')
    content = itertools.chain(wraps[0:1], areas, wraps[1:])
    content = map(smart_bytes, content)  # Workaround Django bug #24240

    if django.get_version() >= '1.5':
        response_type = http.StreamingHttpResponse
    else:
        response_type = http.HttpResponse
        # Django 1.4 middleware messes up iterable content
        content = list(content)

    return response_type(content)


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
    content = map(smart_bytes, content)  # Workaround Django bug #24240

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
