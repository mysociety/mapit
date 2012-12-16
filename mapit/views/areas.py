import re
import operator
from psycopg2.extensions import QueryCanceledError
from psycopg2 import InternalError
try:
    from django.db.utils import DatabaseError
except:
    from psycopg2 import DatabaseError
from osgeo import gdal

from django.contrib.gis.geos import Point
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import resolve, reverse
from django.db.models import Q
from django.conf import settings
from django.shortcuts import redirect

from mapit.models import Area, Generation, Geometry, Code, Name, SimplifiedAway
from mapit.shortcuts import output_json, output_html, render, get_object_or_404, set_timeout
from mapit.middleware import ViewException
from mapit.ratelimitcache import ratelimit
from mapit import countries

def generations(request):
    generations = Generation.objects.all()
    return output_json( dict( (g.id, g.as_dict() ) for g in generations ) )

@ratelimit(minutes=3, requests=100)
def area(request, area_id, format='json'):
    if hasattr(countries, 'area_code_lookup'):
        resp = countries.area_code_lookup(request, area_id, format)
        if resp: return resp


    if not re.match('\d+$', area_id):
        raise ViewException(format, 'Bad area ID specified', 400)


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

    if format == 'html':
        return render(request, 'mapit/area.html', {
            'area': area,
            'codes': codes,
            'alternative_names': alternative_names,
            'geotype': geotype,
        })
    return output_json( area.as_dict(names) )

@ratelimit(minutes=3, requests=100)
def area_polygon(request, srid='', area_id='', format='kml'):
    if not srid and hasattr(countries, 'area_code_lookup'):
        resp = countries.area_code_lookup(request, area_id, format)
        if resp: return resp

    if not re.match('\d+$', area_id):
        raise ViewException(format, 'Bad area ID specified', 400)

    if not srid:
        srid = 4326 if format in ('kml', 'json', 'geojson') else settings.MAPIT_AREA_SRID
    srid = int(srid)

    area = get_object_or_404(Area, id=area_id)

    try:
        simplify_tolerance = float(request.GET.get('simplify_tolerance', 0))
    except ValueError:
        raise ViewException(format, 'Badly specified tolerance', 400)

    try:
        output, content_type = area.export(srid, format, simplify_tolerance=simplify_tolerance)
        if output is None:
            return output_json({'error': 'No polygons found'}, code=404)
    except SimplifiedAway:
        return output_json({'error': 'Simplifying removed all the polygons'}, code=404)

    return HttpResponse(output, content_type='%s; charset=utf-8' % content_type)
    
@ratelimit(minutes=3, requests=100)
def area_children(request, area_id, format='json'):
    area = get_object_or_404(Area, format=format, id=area_id)

    generation = request.REQUEST.get('generation', Generation.objects.current())
    if not generation: generation = Generation.objects.current()
    args = {
        'generation_low__lte': generation,
        'generation_high__gte': generation,
    }

    type = request.REQUEST.get('type', '')
    if ',' in type:
        args['type__code__in'] = type.split(',')
    elif type:
        args['type__code'] = type

    children = add_codes(area.children.filter(**args))

    if format == 'html': return output_html(request, 'Children of %s' % area.name, children)
    return output_json( dict( (child.id, child.as_dict() ) for child in children ) )

def area_intersect(query_type, title, request, area_id, format):
    area = get_object_or_404(Area, format=format, id=area_id)
    if not area.polygons.count():
        raise ViewException(format, 'No polygons found', 404)

    generation = Generation.objects.current()
    types = filter( None, request.REQUEST.get('type', '').split(',') )

    set_timeout(format)
    try:
        # Cast to list so that it's evaluated here, and add_codes doesn't get
        # confused with a RawQuerySet
        areas = list(Area.objects.intersect(query_type, area, types, generation))
        areas = add_codes(areas)
    except QueryCanceledError:
        raise ViewException(format, 'That query was taking too long to compute - try restricting to a specific type, if you weren\'t already doing so.', 500)
    except DatabaseError, e:
        # Django 1.2+ catches QueryCanceledError and throws its own DatabaseError instead
        if 'canceling statement due to statement timeout' not in e.args[0]: raise
        raise ViewException(format, 'That query was taking too long to compute - try restricting to a specific type, if you weren\'t already doing so.', 500)
    except InternalError:
        raise ViewException(format, 'There was an internal error performing that query.', 500)

    if format == 'html':
        return output_html(request,
            title % ('<a href="%sarea/%d.html">%s</a>' % (reverse('mapit_index'), area.id, area.name)),
            areas, norobots=True
        )
    return output_json( dict( (a.id, a.as_dict() ) for a in areas ) )

@ratelimit(minutes=3, requests=100)
def area_touches(request, area_id, format='json'):
    # XXX Exempt an error that throws a GEOS Exception
    if area_id == '2658':
        raise ViewException(format, 'There was an internal error performing that query.', 500)
    return area_intersect('touches', 'Areas touching %s', request, area_id, format)

@ratelimit(minutes=3, requests=100)
def area_overlaps(request, area_id, format='json'):
    return area_intersect('overlaps', 'Areas overlapping %s', request, area_id, format)

@ratelimit(minutes=3, requests=100)
def area_covers(request, area_id, format='json'):
    return area_intersect('coveredby', 'Areas covered by %s', request, area_id, format)

@ratelimit(minutes=3, requests=100)
def area_coverlaps(request, area_id, format='json'):
    return area_intersect(['overlaps', 'coveredby'], 'Areas covered by or overlapping %s', request, area_id, format)

@ratelimit(minutes=3, requests=100)
def area_covered(request, area_id, format='json'):
    return area_intersect('covers', 'Areas that cover %s', request, area_id, format)

def add_codes(areas):
    codes = Code.objects.select_related('type').filter(area__in=areas)
    lookup = {}
    for code in codes:
        lookup.setdefault(code.area_id, []).append(code)
    for area in areas:
        if area.id in lookup:
            area.code_list = lookup[area.id]
    return areas

@ratelimit(minutes=3, requests=100)
def areas(request, area_ids, format='json'):
    area_ids = area_ids.split(',')
    areas = add_codes(Area.objects.filter(id__in=area_ids))
    if format == 'html': return output_html(request, 'Areas ID lookup', areas)
    return output_json( dict( ( area.id, area.as_dict() ) for area in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_type(request, type, format='json'):
    generation = Generation.objects.current()
    try:
        min_generation = int(request.REQUEST['min_generation'])
    except:
        min_generation = generation

    args = {}
    if ',' in type:
        args['type__code__in'] = type.split(',')
    elif type:
        args['type__code'] = type

    if min_generation == -1:
        areas = add_codes(Area.objects.filter(**args))
    else:
        args['generation_low__lte'] = generation
        args['generation_high__gte'] = min_generation
        areas = add_codes(Area.objects.filter(**args))
    if format == 'html':
        return output_html(request, 'Areas in %s' % type, areas)
    return output_json( dict( (a.id, a.as_dict() ) for a in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_name(request, name, format='json'):
    generation = Generation.objects.current()
    try:
        min_generation = int(request.REQUEST['min_generation'])
    except:
        min_generation = generation

    type = request.REQUEST.get('type', '')

    args = {
        'name__istartswith': name,
        'generation_low__lte': generation,
        'generation_high__gte': min_generation,
    }
    if ',' in type:
        args['type__code__in'] = type.split(',')
    elif type:
        args['type__code'] = type

    areas = add_codes(Area.objects.filter(**args))
    if format == 'html': return output_html(request, 'Areas starting with %s' % name, areas)
    out = dict( ( area.id, area.as_dict() ) for area in areas )
    return output_json(out)

@ratelimit(minutes=3, requests=100)
def area_geometry(request, area_id):
    area = _area_geometry(area_id)
    if isinstance(area, HttpResponse): return area
    return output_json(area)

def _area_geometry(area_id):
    area = get_object_or_404(Area, id=area_id)
    all_areas = area.polygons.all().collect()
    if not all_areas:
        return output_json({ 'error': 'No polygons found' }, code=404)
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

@ratelimit(minutes=3, requests=100)
def areas_geometry(request, area_ids):
    area_ids = area_ids.split(',')
    out = {}
    for id in area_ids:
        area = _area_geometry(id)
        if isinstance(area, HttpResponse):
            area = {}
        out[id] = area
    return output_json(out)

@ratelimit(minutes=3, requests=100)
def area_from_code(request, code_type, code_value, format='json'):
    generation = request.REQUEST.get('generation',
                                     Generation.objects.current())
    if not generation:
        generation = Generation.objects.current()
    try:
        area = Area.objects.get(codes__type__code=code_type,
                                codes__code=code_value,
                                generation_low__lte=generation,
                                generation_high__gte=generation)
    except Area.DoesNotExist, e:
        message = 'No areas were found that matched code %s = %s.' % (code_type, code_value)
        raise ViewException(format, message, 404)
    except Area.MultipleObjectsReturned, e:
        message = 'There were multiple areas that matched code %s = %s.' % (code_type, code_value)
        raise ViewException(format, message, 500)
    return HttpResponseRedirect("/area/%d%s" % (area.id, '.%s' % format if format else ''))

@ratelimit(minutes=3, requests=100)
def areas_by_point(request, srid, x, y, bb=False, format='json'):
    type = request.REQUEST.get('type', '')
    generation = request.REQUEST.get('generation', Generation.objects.current())
    if not generation: generation = Generation.objects.current()

    location = Point(float(x), float(y), srid=int(srid))
    gdal.UseExceptions()
    try:
        location.transform(settings.MAPIT_AREA_SRID, clone=True)
    except:
        raise ViewException(format, 'Point outside the area geometry', 400)

    method = 'box' if bb and bb != 'polygon' else 'polygon'

    args = { 'generation_low__lte': generation, 'generation_high__gte': generation }

    if ',' in type:
        args['type__code__in'] = type.split(',')
    elif type:
        args['type__code'] = type

    if type and method == 'polygon':
        args = dict( ("area__%s" % k, v) for k, v in args.items() )
        # So this is odd. It doesn't matter if you specify types, PostGIS will
        # do the contains test on all the geometries matching the bounding-box
        # index, even if it could be much quicker to filter some out first
        # (ie. the EUR ones).
        args['polygon__bbcontains'] = location
        shapes = Geometry.objects.filter(**args).defer('polygon')
        areas = []
        for shape in shapes:
            try:
                areas.append( Area.objects.get(polygons__id=shape.id, polygons__polygon__contains=location) )
            except:
                pass
    else:
        if method == 'box':
            args['polygons__polygon__bbcontains'] = location
        else:
            geoms = list(Geometry.objects.filter(polygon__contains=location).defer('polygon'))
            args['polygons__in'] = geoms
        areas = Area.objects.filter(**args)

    areas = add_codes(areas)
    if format == 'html': return output_html(request, 'Areas containing (%s,%s)' % (x,y), areas, indent_areas=True)
    return output_json( dict( (area.id, area.as_dict() ) for area in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_point_latlon(request, lat, lon, bb=False, format=''):
    return HttpResponseRedirect("/point/4326/%s,%s%s%s" % (lon, lat, "/box" if bb else '', '.%s' % format if format else ''))

@ratelimit(minutes=3, requests=100)
def areas_by_point_osgb(request, e, n, bb=False, format=''):
    return HttpResponseRedirect("/point/27700/%s,%s%s%s" % (e, n, "/box" if bb else '', '.%s' % format if format else ''))

def point_form_submitted(request):
    latlon = request.POST.get('pc', None)
    if not request.method == 'POST' or not latlon:
        return redirect('/')
    m = re.match('\s*([0-9.-]+)\s*,\s*([0-9.-]+)', latlon)
    if not m:
        return redirect('/')
    lat, lon = m.groups()
    return redirect('mapit.views.areas.areas_by_point',
        srid=4326, x=lon, y=lat, format='html'
    )

# ---

def deal_with_POST(request, call='areas'):
    url = request.POST.get('URL', '')
    if not url:
        return output_json({ 'error': 'No content specified' }, code=400)
    view, args, kwargs = resolve('/%s/%s' % (call, url))
    kwargs['request'] = request
    return view(*args, **kwargs)

