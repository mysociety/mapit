import itertools

from django import http
from django.db import connection
from django.conf import settings
from django.shortcuts import get_object_or_404 as orig_get_object_or_404
from django.template import loader
from django.utils.six.moves import map
from django.utils.translation import ugettext as _

from mapit.iterables import defaultiter

from django.core.serializers.json import DjangoJSONEncoder


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
    tpl = loader.render_to_string('mapit/data.html', kwargs, request=request)
    wraps = tpl.split('!!!DATA!!!')

    indent_areas = kwargs.get('indent_areas', False)
    item_tpl = loader.get_template('mapit/areas_item.html')
    areas = map(lambda area: item_tpl.render({'area': area, 'indent_areas': indent_areas}), areas)
    areas = defaultiter(areas, '<li>' + _('No matching areas found.') + '</li>')
    content = itertools.chain(wraps[0:1], areas, wraps[1:])

    return http.StreamingHttpResponse(content)


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

    # We don't want a generator function (iterencode) to be passed to an
    # HttpResponse, as it won't cache due to its close() function adding it to
    # an instance attribute.
    content = map(lambda x: x, content)

    types = {
        400: http.HttpResponseBadRequest,
        404: http.HttpResponseNotFound,
        500: http.HttpResponseServerError,
    }
    response_type = types.get(code, http.StreamingHttpResponse)

    response = response_type(content_type='application/json; charset=utf-8')
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'max-age=2419200'  # 4 weeks
    attr = 'streaming_content' if getattr(response, 'streaming', None) else 'content'
    setattr(response, attr, content)
    return response


def output_polygon(content_type, output):
    response = http.HttpResponse(content_type='%s; charset=utf-8' % content_type)
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'max-age=2419200'  # 4 weeks
    response.write(output)
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
