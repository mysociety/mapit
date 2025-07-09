import re
from psycopg2 import InternalError
from django.db.utils import DatabaseError

from django.utils.translation import gettext as _
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models import Collect
from django.db.models import Q, prefetch_related_objects
from django.db.models.query import QuerySet
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import resolve, reverse, NoReverseMatch
from django.conf import settings
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt

from mapit.models import Area, Generation, Code, Name
from mapit.shortcuts import output_json, output_html, output_polygon, get_object_or_404, set_timeout
from mapit.middleware import ViewException
from mapit.ratelimitcache import ratelimit
from mapit.utils import re_number
from mapit import countries
from mapit.iterables import iterdict
from mapit.geometryserialiser import GeometrySerialiser, TransformError


def add_codes(areas):
    """Given an iterable of areas, return an iterator of those areas with codes
    and m2m countries attached. We don't use prefetch_related because this can
    use a lot of memory."""
    codes = Code.objects.select_related('type').filter(area__in=areas)
    countries = Area.countries.through.objects.select_related('country').filter(area__in=areas)

    lookup = {}
    lookup_countries = {}
    for code in codes.iterator():
        lookup.setdefault(code.area_id, {})[code.type.code] = code.code
    for m2m in countries.iterator():
        c = m2m.country
        lookup_countries.setdefault(m2m.area_id, []).append({'code': c.code, 'name': c.name})

    if isinstance(areas, QuerySet):
        if hasattr(countries, 'sorted_areas'):
            areas = countries.sorted_areas(areas)
        areas = areas.iterator()

    for area in areas:
        area.all_codes = lookup.get(area.id, {})
        area.all_m2m_countries = lookup_countries.get(area.id, [])
        yield area


def output_areas(request, title, format, areas, **kwargs):
    areas = add_codes(areas)
    if format == 'map.html':
        format = 'html'
        kwargs['show_map'] = True
    if format == 'html':
        return output_html(request, title, areas, **kwargs)
    return output_json(iterdict((area.id, area.as_dict()) for area in areas))


def query_args(request, format, type=None):
    query = Generation.objects.query_args(request, format)

    if type is None:
        type = request.GET.get('type', '')
    country_code = request.GET.get('country', '')

    for attr, value in [
            (['type'], type),
            (['country', 'countries'], country_code),
    ]:
        q = Q()
        for a in attr:
            if ',' in value:
                q |= Q(**{a + '__code__in': value.split(',')})
            elif value:
                q |= Q(**{a + '__code': value})
        query &= q

    return query


def query_args_polygon(request, format, srid):
    args = {}
    if not srid:
        srid = 4326 if format in ('kml', 'json', 'geojson') else settings.MAPIT_AREA_SRID
    args['srid'] = int(srid)

    try:
        args['simplify_tolerance'] = float(request.GET.get('simplify_tolerance', 0))
    except ValueError:
        raise ViewException(format, _('Badly specified tolerance'), 400)

    return args


def check_area_ids(format, area_ids):
    for area_id in area_ids:
        if not re.match(r'\d+$', area_id):
            raise ViewException(format, _('Bad area ID specified'), 400)


def generations(request, format=''):
    generations = Generation.objects.all()
    if format == 'html':
        return render(request, 'mapit/generations.html', {'generations': generations})
    return output_json(dict((g.id, g.as_dict()) for g in generations))


@ratelimit
def area(request, area_id, format=''):
    if hasattr(countries, 'area_code_lookup'):
        resp = countries.area_code_lookup(request, area_id, format)
        if resp:
            return resp

    if not re.match(r'\d+$', area_id):
        raise ViewException(format, _('Bad area ID specified'), 400)

    area = get_object_or_404(Area, format=format, id=area_id)

    codes = []
    for code_type, code in sorted(area.all_codes.items()):
        code_link = None
        if code_type in ('osm', 'osm_rel'):
            code_link = 'http://www.openstreetmap.org/browse/relation/' + code
        elif code_type == 'osm_way':
            code_link = 'http://www.openstreetmap.org/browse/way/' + code
        codes.append((code_type, code, code_link))

    # Sort any alternative names by the description of the name (the
    # English name of the language for global MapIt) and exclude the
    # default OSM name, since if that exists, it'll already be
    # displayed as the page title.

    names = Name.objects.filter(area=area).select_related()
    alternative_names = sorted((n.type.description, n.name) for n in names
                               if n.type.code != "default")

    geotype = {}
    if hasattr(countries, 'restrict_geo_html'):
        geotype = countries.restrict_geo_html(area)

    active_generation = Generation.objects.current()

    if format == 'html':
        return render(request, 'mapit/area.html', {
            'active_generation': active_generation,
            'area': area,
            'codes': codes,
            'alternative_names': alternative_names,
            'geotype': geotype,
        })
    return output_json(area.as_dict(names))


@ratelimit
def area_polygon(request, srid='', area_id='', format='kml'):
    if not srid and hasattr(countries, 'area_code_lookup'):
        resp = countries.area_code_lookup(request, area_id, format)
        if resp:
            return resp

    args = query_args_polygon(request, format, srid)
    check_area_ids(format, [area_id])

    area = get_object_or_404(Area, id=area_id)

    try:
        output, content_type = area.export(args['srid'], format, simplify_tolerance=args['simplify_tolerance'])
        if output is None:
            return output_json({'error': _('No polygons found')}, code=404)
    except TransformError as e:
        return output_json({'error': e.args[0]}, code=400)

    return output_polygon(content_type, output)


@ratelimit
def area_children(request, area_id, format=''):
    q = query_args(request, format)
    area = get_object_or_404(Area, format=format, id=area_id)
    children = area.children.filter(q).distinct()
    if format in ('kml', 'geojson'):
        return _areas_polygon(request, format, children)
    return output_areas(request, _('Children of %s') % area.name, format, children)


def area_intersect(query_type, title, request, area_id, format):
    area = get_object_or_404(Area, format=format, id=area_id)
    if not area.polygons.count():
        raise ViewException(format, _('No polygons found'), 404)

    generation = Generation.objects.current()
    types = [_f for _f in request.GET.get('type', '').split(',') if _f]

    set_timeout(format)
    try:
        # Cast to list so that it's evaluated here, and output_areas doesn't get
        # confused with a RawQuerySet
        areas = list(Area.objects.intersect(query_type, area, types, generation))
    except DatabaseError as e:
        if 'canceling statement due to statement timeout' not in e.args[0] \
           and 'canceling statement due to user request' not in e.args[0]:
            raise
        raise ViewException(
            format, _('That query was taking too long to compute - '
                      'try restricting to a specific type, if you weren\'t already doing so.'), 500)
    except InternalError:
        raise ViewException(format, _('There was an internal error performing that query.'), 500)

    # Each object will need type which hasn't been fetched by the RawQuerySet
    prefetch_related_objects(areas, 'type')

    title = title % ('<a href="%sarea/%d.html">%s</a>' % (reverse('mapit_index'), area.id, area.name))
    return output_areas(request, title, format, areas, norobots=True)


@ratelimit
def area_touches(request, area_id, format=''):
    return area_intersect('touches', _('Areas touching %s'), request, area_id, format)


@ratelimit
def area_overlaps(request, area_id, format=''):
    return area_intersect('overlaps', _('Areas overlapping %s'), request, area_id, format)


@ratelimit
def area_covers(request, area_id, format=''):
    return area_intersect('coveredby', _('Areas covered by %s'), request, area_id, format)


@ratelimit
def area_coverlaps(request, area_id, format=''):
    return area_intersect(['overlaps', 'coveredby'], _('Areas covered by or overlapping %s'), request, area_id, format)


@ratelimit
def area_covered(request, area_id, format=''):
    return area_intersect('covers', _('Areas that cover %s'), request, area_id, format)


@ratelimit
def area_intersects(request, area_id, format=''):
    return area_intersect('intersects', _('Areas that intersect %s'), request, area_id, format)


@ratelimit
def areas(request, area_ids, format=''):
    area_ids = area_ids.split(',')
    areas = Area.objects.filter(id__in=area_ids)
    return output_areas(request, _('Areas ID lookup'), format, areas)


@ratelimit
def areas_by_type(request, type, format=''):
    q = query_args(request, format, type)
    areas = Area.objects.filter(q).distinct()
    if format in ('kml', 'geojson'):
        return _areas_polygon(request, format, areas)
    return output_areas(request, _('Areas in %s') % type, format, areas)


@ratelimit
def areas_by_name(request, name, format=''):
    q = query_args(request, format)
    q &= Q(name__istartswith=name)
    areas = Area.objects.filter(q).distinct()
    return output_areas(request, _('Areas starting with %s') % name, format, areas)


@ratelimit
def areas_polygon(request, area_ids, srid='', format='kml'):
    area_ids = area_ids.split(',')
    check_area_ids(format, area_ids)

    areas = list(Area.objects.filter(id__in=area_ids))
    if not areas:
        return output_json({'error': _('No areas found')}, code=404)

    return _areas_polygon(request, format, areas, srid)


def _areas_polygon(request, format, areas, srid=None):
    args = query_args_polygon(request, format, srid)
    areas = add_codes(areas)
    serialiser = GeometrySerialiser(list(areas), args['srid'], args['simplify_tolerance'])

    try:
        if format == 'kml':
            output, content_type = serialiser.kml('full')
        elif format == 'geojson':
            output, content_type = serialiser.geojson()
    except TransformError as e:
        return output_json({'error': e.args[0]}, code=400)

    return output_polygon(content_type, output)


@ratelimit
def area_geometry(request, area_id):
    area = _area_geometry(area_id)
    if isinstance(area, HttpResponse):
        return area
    return output_json(area)


def _area_geometry(area_id):
    area = get_object_or_404(Area, id=area_id)
    all_areas = area.polygons.all().aggregate(Collect('polygon'))['polygon__collect']
    if not all_areas:
        return output_json({'error': _('No polygons found')}, code=404)
    out = {
        'parts': all_areas.num_geom,
    }
    if settings.MAPIT_AREA_SRID != 4326:
        out['srid_en'] = settings.MAPIT_AREA_SRID
        out['area'] = all_areas.area
        out['min_e'], out['min_n'], out['max_e'], out['max_n'] = all_areas.extent
        out['centre_e'], out['centre_n'] = all_areas.centroid
        all_areas.transform(4326)
        out['min_lon'], out['min_lat'], out['max_lon'], out['max_lat'] = all_areas.extent
        out['centre_lon'], out['centre_lat'] = all_areas.centroid
    else:
        out['min_lon'], out['min_lat'], out['max_lon'], out['max_lat'] = all_areas.extent
        out['centre_lon'], out['centre_lat'] = all_areas.centroid
        if hasattr(countries, 'area_geometry_srid'):
            srid = countries.area_geometry_srid
            all_areas.transform(srid)
            out['srid_en'] = srid
            out['area'] = all_areas.area
            out['min_e'], out['min_n'], out['max_e'], out['max_n'] = all_areas.extent
            out['centre_e'], out['centre_n'] = all_areas.centroid
    return out


@ratelimit
def areas_geometry(request, area_ids):
    area_ids = area_ids.split(',')
    out = {}
    for id in area_ids:
        area = _area_geometry(id)
        if isinstance(area, HttpResponse):
            area = {}
        out[id] = area
    return output_json(out)


@ratelimit
def area_from_code(request, code_type, code_value, format='', area_type=None):
    q = query_args(request, format, area_type)
    q &= Q(codes__type__code=code_type, codes__code=code_value)

    try:
        area = Area.objects.get(q)
    except Area.DoesNotExist:
        message = _('No areas were found that matched code {0} = {1}.').format(code_type, code_value)
        raise ViewException(format, message, 404)
    except Area.MultipleObjectsReturned:
        message = _('There were multiple areas that matched code {0} = {1}.').format(code_type, code_value)
        raise ViewException(format, message, 500)

    area_kwargs = {'area_id': area.id}
    if format:
        area_kwargs['format'] = format

    # As well as /code we could be called (via area_code_lookup) by either area or area_polygon
    try:
        redirect_path = reverse('area', kwargs=area_kwargs)
    except NoReverseMatch:
        redirect_path = reverse('area_polygon', kwargs=area_kwargs)

    # If there was a query string, make sure it's passed on in the
    # redirect:
    if request.META['QUERY_STRING']:
        redirect_path += "?" + request.META['QUERY_STRING']
    return HttpResponseRedirect(redirect_path)


@ratelimit
def areas_by_point(request, srid, x, y, bb=False, format=''):
    location = Point(float(x), float(y), srid=int(srid))

    use_exceptions()

    try:
        location.transform(settings.MAPIT_AREA_SRID, clone=True)
    except:
        raise ViewException(format, _('Point outside the area geometry'), 400)

    method = 'box' if bb and bb != 'polygon' else 'polygon'

    q = query_args(request, format)

    max_within = getattr(settings, 'MAPIT_WITHIN_MAXIMUM', 0)
    try:
        within = float(request.GET.get('within', 0))
        if within < 0 or within > max_within:
            raise ValueError
    except ValueError:
        raise ViewException(format, _('Bad "within" parameter specified'), 400)

    if method == 'box':
        q &= Q(polygons__subdivided__division__bbcovers=location)
    elif within:
        q &= Q(polygons__subdivided__division__dwithin=(location, within))
    else:
        q &= Q(polygons__subdivided__division__covers=location)
    areas = Area.objects.filter(q).distinct()

    return output_areas(
        request, _('Areas covering the point ({0},{1})').format(x, y),
        format, areas, indent_areas=True)


def _areas_by_point(x, y, srid, **kwargs):
    kwargs.update({'srid': srid, 'x': kwargs.pop(x), 'y': kwargs.pop(y)})
    kwargs = {k: v for k, v in kwargs.items() if v}
    redirect_path = reverse('areas-by-point', kwargs=kwargs)
    return HttpResponseRedirect(redirect_path)


@ratelimit
def areas_by_point_latlon(request, **kwargs):
    return _areas_by_point('lon', 'lat', 4326, **kwargs)


@ratelimit
def areas_by_point_osgb(request, **kwargs):
    return _areas_by_point('e', 'n', 27700, **kwargs)


@csrf_exempt
def point_form_submitted(request):
    latlon = request.POST.get('pc', '')
    if not request.method == 'POST' or not latlon:
        return redirect('mapit_index')
    m = re.match(r'\s*(%s)\s*,\s*(%s)' % (re_number, re_number), latlon)
    if not m:
        return redirect('mapit_index')
    lat, lon = m.groups()
    return redirect(
        'areas-by-point',
        srid=4326, x=lon, y=lat, format='html'
    )

# ---


@csrf_exempt
def deal_with_POST(request, call='areas'):
    url = request.POST.get('URL', '')
    if not url:
        return output_json({'error': _('No content specified')}, code=400)
    view, args, kwargs = resolve('/%s/%s' % (call, url))
    request.GET = request.POST
    kwargs['request'] = request
    return view(*args, **kwargs)


def use_exceptions():
    if not hasattr(use_exceptions, 'done'):
        use_exceptions.done = True
        try:
            from osgeo import gdal
            gdal.UseExceptions()
        except ImportError:
            pass
