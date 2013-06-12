import re
from django.utils import simplejson
from django import http
from django.db import connection
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404 as orig_get_object_or_404
from django.shortcuts import render_to_response
from django.template import RequestContext
from lxml import etree

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

def sorted_areas(areas):
    # In here to prevent a circular dependency
    from mapit import countries
    if hasattr(countries, 'sorted_areas'):
        return countries.sorted_areas(areas)
    return list(areas)

def output_html(request, title, areas, **kwargs):
    kwargs['json_url'] = request.path.replace('.html', '')
    kwargs['title'] = title
    kwargs['areas'] = sorted_areas(areas)
    kwargs['indent_areas'] = kwargs.get('indent_areas', False)
    return render(request, 'mapit/data.html', kwargs)

def output_multiple_kml(request, title, areas):
    """Return a KML file with a NetworkLink to KML for each area"""

    kml = etree.Element("kml",
                        nsmap={None: "http://earth.google.com/kml/2.1"})
    folder = etree.SubElement(kml, "Folder")
    etree.SubElement(folder, "name").text = title
    etree.SubElement(folder, "visibility").text = "1"
    etree.SubElement(folder, "open").text = "0"
    description = u'A KML file that links to results for ' + title
    etree.SubElement(folder, "description").text = description
    for area in areas:
        network_link = etree.SubElement(folder,
                                        'NetworkLink',
                                        attrib={'id': str(area.id)})
        etree.SubElement(network_link, "name").text = area.name
        etree.SubElement(network_link, "visibility").text = "1"
        etree.SubElement(network_link, "open").text = "0"
        area_description = '%s (MapIt area ID: %d)' % (area.name, area.id)
        etree.SubElement(network_link, "description").text = area_description
        etree.SubElement(network_link, "flyToView").text = "0"
        link = etree.SubElement(network_link, "Link")
        etree.SubElement(link, "href").text = request.build_absolute_uri(
            reverse('mapit.views.areas.area',
                    kwargs={'area_id': area.id}))
    return http.HttpResponse(
        etree.tostring(kml,
                       pretty_print=True,
                       encoding="utf-8",
                       xml_declaration=True),
        content_type='application/vnd.google-earth.kml+xml')

def output_json(out, code=200):
    types = {
        400: http.HttpResponseBadRequest,
        404: http.HttpResponseNotFound,
        500: http.HttpResponseServerError,
    }
    response_type = types.get(code, http.HttpResponse)
    response = response_type(content_type='application/json; charset=utf-8')
    response['Access-Control-Allow-Origin'] = '*'
    response['Cache-Control'] = 'max-age=2419200' # 4 weeks
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
        from mapit.middleware import ViewException
        raise ViewException(format, str(e), 404)

def json_500(request):
    return output_json({ 'error': "Sorry, something's gone wrong." }, code=500)

def set_timeout(format):
    cursor = connection.cursor()
    timeout = 10000 if format == 'html' else 10000
    cursor.execute('set session statement_timeout=%d' % timeout)

