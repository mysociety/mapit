import re
import operator
from psycopg2.extensions import QueryCanceledError
from psycopg2 import InternalError
try:
    from django.db.utils import DatabaseError
except:
    from psycopg2 import DatabaseError
from osgeo import gdal
from mapit.areas.models import Area, Generation, Geometry, Code
from mapit.shortcuts import output_json, output_html, render, get_object_or_404, output_error, set_timeout
from mapit.ratelimitcache import ratelimit
from django.contrib.gis.geos import Point
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import resolve
from django.db.models import Q
import mysociety.config

voting_area = {
    'type_name': {
        'LBO':  "London Borough",
        'LBW':  "Ward",
        'GLA':  "Greater London Authority",
        'LAS':  "London Assembly",
        'LAC':  "Constituency",
        'LAE':  "Electoral Region",
        'CTY':  "County",
        'CED':  "Electoral Division",
        'DIS':  "District",
        'DIW':  "Ward",
        'LGD':  "Local Council",
        'LGE':  "Electoral Area",
        'UTA':  "Unitary Authority",
        'UTE':  "Electoral Division",
        'UTW':  "Ward",
        'MTD':  "Metropolitan District",
        'MTW':  "Ward",
        'COI':  "Council of the Isles",
        'COP':  "Parish",
        'SPA':  "Scottish Parliament",
        'SPE':  "Electoral Region",
        'SPC':  "Constituency",
        'WAS':  "National Assembly for Wales",
        'WAE':  "Electoral Region",
        'WAC':  "Constituency",
        'NIA':  "Northern Ireland Assembly",
        'NIE':  "Constituency", # These are the same as the Westminster
                                # constituencies but return several members
                                # using a proportional system. It looks like
                                # most people just refer to them as
                                # "constituencies".
        'WMP':  "House of Commons",
        'WMC':  "Constituency",
        'HOL':  "House of Lords",
        'HOC':  "Constituency",
        'EUP':  "European Parliament",
        'EUR':  "Region",
    },
    'attend_prep': {
        'LBO':  "on",
        'LAS':  "on the",
        'CTY':  "on",
        'DIS':  "on",
        'UTA':  "on",
        'MTD':  "on",
        'COI':  "on",
        'LGD':  "on",
        'SPA':  "in the",
        'WAS':  "on the",
        'NIA':  "on the",
        'WMP':  "in the",
        'HOL':  "in the",
        'EUP':  "in the",
    },
    'general_prep': {
        'LBO':  "",
        'LAS':  "the",
        'CTY':  "",
        'DIS':  "",
        'UTA':  "",
        'MTD':  "",
        'COI':  "",
        'LGD':  "",
        'SPA':  "the",
        'WAS':  "the",
        'NIA':  "the",
        'WMP':  "the",
        'HOL':  "the",
        'EUP':  "the",

    },
    'rep_name': {
        'LBW': 'Councillor',
        'GLA': 'Mayor', # "of London"? 
        'LAC': 'London Assembly Member',
        'LAE': 'London Assembly Member',
        'CED': 'County Councillor',
        'DIW': 'District Councillor',
        'LGE': 'Councillor',
        'UTE': 'Councillor',
        'UTW': 'Councillor',
        'MTW': 'Councillor',
        'COP': 'Councillor',
        'SPE': 'MSP',
        'SPC': 'MSP',
        'WAE': 'AM',
        'WAC': 'AM',
        'NIE': 'MLA',
        'WMC': 'MP',
        'HOC': 'Lord',
        'EUR': 'MEP',
    },
    'rep_name_plural': {
        'LBW': 'Councillors',
        'GLA': 'Mayors', # "of London"?
        'LAC': 'London Assembly Members',
        'LAE': 'London Assembly Members',
        'CED': 'County Councillors',
        'DIW': 'District Councillors',
        'UTE': 'Councillors',
        'UTW': 'Councillors',
        'LGE': 'Councillors',
        'MTW': 'Councillors',
        'COP': 'Councillors',
        'SPE': 'MSPs',
        'SPC': 'MSPs',
        'WAE': 'AMs',
        'WAC': 'AMs',
        'NIE': 'MLAs',
        'WMC': 'MPs',
        'HOC': 'Lords',
        'EUR': 'MEPs'
    },
    'rep_name_long': {
        'LBW': 'Councillor',
        'GLA': 'Mayor', # "of London"? 
        'LAC': 'London Assembly Member',
        'LAE': 'London Assembly Member',
        'CED': 'County Councillor',
        'DIW': 'District Councillor',
        'LGE': 'Councillor',
        'UTE': 'Councillor',
        'UTW': 'Councillor',
        'MTW': 'Councillor',
        'COP': 'Councillor',
        'SPE': 'Member of the Scottish Parliament',
        'SPC': 'Member of the Scottish Parliament',
        'NIE': 'Member of the Legislative Assembly',
        'WAE': 'Assembly Member',
        'WAC': 'Assembly Member',
        'WMC': 'Member of Parliament',
        'HOC': 'Member of Parliament',
        'EUR': 'Member of the European Parliament'
    },
    'rep_name_long_plural': {
        'LBW': 'Councillors',
        'GLA': 'Mayors', # "of London"?
        'LAC': 'London Assembly Members',
        'LAE': 'London Assembly Members',
        'CED': 'County Councillors',
        'DIW': 'District Councillors',
        'UTE': 'Councillors',
        'UTW': 'Councillors',
        'LGE': 'Councillors',
        'MTW': 'Councillors',
        'COP': 'Councillors',
        'SPE': 'Members of the Scottish Parliament',
        'SPC': 'Members of the Scottish Parliament',
        'WAE': 'Assembly Members',
        'WAC': 'Assembly Members',
        'NIE': 'Members of the Legislative Assembly',
        'WMC': 'Members of Parliament',
        'HOC': 'Members of Parliament',
        'EUR': 'Members of the European Parliament'
    },
    'rep_suffix': {
        'LBW': '',
        'GLA': '',
        'LAC': 'AM',
        'LAE': 'AM',
        'CED': '',
        'DIW': '',
        'UTE': '',
        'UTW': '',
        'LGE': '',
        'MTW': '',
        'COP': '',
        'SPE': 'MSP',
        'SPC': 'MSP',
        'WAE': 'AM',
        'WAC': 'AM',
        'NIE': 'MLA',
        'WMC': 'MP',
        'HOC': '', # has neither prefix or suffix as titles in names
        'EUR': 'MEP'
    },
    'rep_prefix': {
        'LBW': 'Cllr',
        'GLA': 'Mayor', # "of London"? 
        'LAC': '',
        'LAE': '',
        'CED': 'Cllr',
        'DIW': 'Cllr',
        'UTE': 'Cllr',
        'UTW': 'Cllr',
        'LGE': 'Cllr',
        'MTW': 'Cllr',
        'COP': 'Cllr',
        'SPE': '',
        'SPC': '',
        'WAE': '',
        'WAC': '',
        'NIE': '',
        'WMC': '',
        'HOC': '', # has neither prefix or suffix as titles in names
        'EUR': ''
    }
}

def generations(request):
    generations = Generation.objects.all()
    return output_json( dict( (g.id, g.as_dict() ) for g in generations ) )

@ratelimit(minutes=3, requests=100)
def area(request, area_id, format='json'):
    if re.match('\d\d([A-Z]{2}|[A-Z]{4}|[A-Z]{2}\d\d\d|[A-Z]|[A-Z]\d\d)$', area_id):
        area = get_object_or_404(Area, format=format, codes__type='ons', codes__code=area_id)
    elif re.match('[ENSW]\d{8}$', area_id):
        area = get_object_or_404(Area, format=format, codes__type='gss', codes__code=area_id)
    elif not re.match('\d+$', area_id):
        return output_error(format, 'Bad area ID specified', 400)
    else:
        area = get_object_or_404(Area, format=format, id=area_id)
    if isinstance(area, HttpResponse): return area
    if format == 'html':
        return render(request, 'area.html', {
            'area': area,
            'show_geometry': (area.type not in ('EUR', 'SPE', 'WAE'))
        })
    return output_json( area.as_dict() )

@ratelimit(minutes=3, requests=100)
def area_polygon(request, srid='', area_id='', format='kml'):
    if not srid:
        srid = 4326 if format in ('kml', 'json', 'geojson') else int(mysociety.config.get('AREA_SRID'))
    srid = int(srid)
    area = get_object_or_404(Area, id=area_id)
    if isinstance(area, HttpResponse): return area
    all_areas = area.polygons.all()
    if len(all_areas) > 1:
        all_areas = all_areas.collect()
    elif len(all_areas) == 1:
        all_areas = all_areas[0].polygon
    else:
        return output_json({ 'error': 'No polygons found' }, code=404)
    if srid != int(mysociety.config.get('AREA_SRID')):
        all_areas.transform(srid)

    try:
        simplify_tolerance = float(request.GET.get('simplify_tolerance', 0))
    except:
        return output_error(format, 'Badly specified tolerance', 400)
    if simplify_tolerance:
        all_areas = all_areas.simplify(simplify_tolerance)

    if format=='kml':
        out = '''<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
    <Placemark>
        <name>%s</name>
        %s
    </Placemark>
</kml>''' % (area.name, all_areas.kml)
        content_type = 'application/vnd.google-earth.kml+xml'
    elif format in ('json', 'geojson'):
        out = all_areas.json
        content_type = 'application/json'
    elif format=='wkt':
        out = all_areas.wkt
        content_type = 'text/plain'
    return HttpResponse(out, content_type='%s; charset=utf-8' % content_type)
    
@ratelimit(minutes=3, requests=100)
def area_children(request, area_id, legacy=False, format='json'):
    area = get_object_or_404(Area, format=format, id=area_id)
    if isinstance(area, HttpResponse): return area

    generation = Generation.objects.current()
    args = {
        'generation_low__lte': generation,
        'generation_high__gte': generation,
    }

    type = request.REQUEST.get('type', '')
    if ',' in type:
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type

    children = add_codes(area.children.filter(**args))

    if legacy: return output_json( [ child.id for child in children ] )
    if format == 'html': return output_html(request, 'Children of %s' % area.name, children)
    return output_json( dict( (child.id, child.as_dict() ) for child in children ) )

def area_intersect(query_type, title, request, area_id, format):
    area = get_object_or_404(Area, format=format, id=area_id)
    if isinstance(area, HttpResponse): return area

    if not area.polygons.count():
        return output_error(format, 'No polygons found', 404)

    generation = Generation.objects.current()
    args = {
        'generation_low__lte': generation,
        'generation_high__gte': generation,
    }

    type = request.REQUEST.get('type', '')
    if ',' in type:
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type
    elif area.type in ('EUR'):
        args['type'] = area.type

    areas = Area.objects.intersect(query_type, area).exclude(id=area.id).filter(**args).distinct()

    set_timeout(format)
    try:
        if format == 'html':
            return output_html(request,
                title % ('<a href="/area/%d.html">%s</a>' % (area.id, area.name)),
                areas, norobots=True
            )
        return output_json( dict( (a.id, a.as_dict() ) for a in areas ) )
    except QueryCanceledError:
        return output_error(format, 'That query was taking too long to compute - try restricting to a specific type, if you weren\'t already doing so.', 500)
    except DatabaseError, e:
        # Django 1.2+ catches QueryCanceledError and throws its own DatabaseError instead
        if 'canceling statement due to statement timeout' not in e.args[0]: raise
        return output_error(format, 'That query was taking too long to compute - try restricting to a specific type, if you weren\'t already doing so.', 500)
    except InternalError:
        return output_error(format, 'There was an internal error performing that query.', 500)

@ratelimit(minutes=3, requests=100)
def area_touches(request, area_id, format='json'):
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
    codes = Code.objects.filter(area__in=areas)
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
def areas_by_type(request, type, legacy=False, format='json'):
    generation = Generation.objects.current()
    try:
        min_generation = int(request.REQUEST['min_generation'])
    except:
        min_generation = generation

    args = {}
    if ',' in type:
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type

    if min_generation == -1:
        areas = add_codes(Area.objects.filter(**args))
    else:
        args['generation_low__lte'] = generation
        args['generation_high__gte'] = min_generation
        areas = add_codes(Area.objects.filter(**args))
    if format == 'html':
        return output_html(request, 'Areas in %s' % type, areas)
    elif legacy: return output_json( [ a.id for a in areas ] )
    return output_json( dict( (a.id, a.as_dict() ) for a in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_name(request, name, legacy=False, format='json'):
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
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type

    areas = add_codes(Area.objects.filter(**args))
    if legacy:
        out = dict( (area.id, {
            'area_id': area.id,
            'name': area.name,
            'type': area.type,
            'parent_area_id': area.parent_area_id,
        }) for area in areas )
    else:
        out = dict( ( area.id, area.as_dict() ) for area in areas )
    if format == 'html': return output_html(request, 'Areas starting with %s' % name, areas)
    return output_json(out)

@ratelimit(minutes=3, requests=100)
def area_geometry(request, area_id):
    area = _area_geometry(area_id)
    if isinstance(area, HttpResponse): return area
    return output_json(area)

def _area_geometry(area_id):
    area = get_object_or_404(Area, id=area_id)
    if isinstance(area, HttpResponse): return area
    all_areas = area.polygons.all().collect()
    if not all_areas:
        return output_json({ 'error': 'No polygons found' }, code=404)
    out = {
        'parts': all_areas.num_geom,
    }
    if int(mysociety.config.get('AREA_SRID')) != 4326:
        out['srid_en'] = mysociety.config.get('AREA_SRID')
        out['area'] = all_areas.area
        out['min_e'], out['min_n'], out['max_e'], out['max_n'] = all_areas.extent
        out['centre_e'], out['centre_n'] = all_areas.centroid
        all_areas.transform(4326)
        out['min_lon'], out['min_lat'], out['max_lon'], out['max_lat'] = all_areas.extent
        out['centre_lon'], out['centre_lat'] = all_areas.centroid
    elif mysociety.config.get('COUNTRY') == 'NO':
        out['min_lon'], out['min_lat'], out['max_lon'], out['max_lat'] = all_areas.extent
        out['centre_lon'], out['centre_lat'] = all_areas.centroid
        all_areas.transform(32633)
        out['srid_en'] = 32633
        out['area'] = all_areas.area
        out['min_e'], out['min_n'], out['max_e'], out['max_n'] = all_areas.extent
        out['centre_e'], out['centre_n'] = all_areas.centroid
    return out

@ratelimit(minutes=3, requests=100)
def areas_geometry(request, area_ids):
    area_ids = area_ids.split(',')
    out = dict( (id, _area_geometry(id)) for id in area_ids )
    return output_json(out)

@ratelimit(minutes=3, requests=100)
def areas_by_point(request, srid, x, y, bb=False, legacy=False, format='json'):
    type = request.REQUEST.get('type', '')
    generation = request.REQUEST.get('generation', Generation.objects.current())
    if not generation: generation = Generation.objects.current()

    location = Point(float(x), float(y), srid=int(srid))
    gdal.UseExceptions()
    try:
        location.transform(mysociety.config.get('AREA_SRID'), clone=True)
    except:
        return output_error(format, 'Point outside the area geometry', 400)

    method = 'box' if bb and bb != 'polygon' else 'polygon'

    args = { 'generation_low__lte': generation, 'generation_high__gte': generation }

    if ',' in type:
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type

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

    if legacy: return output_json( dict( (area.id, area.type) for area in areas ) )
    if format == 'html': return output_html(request, 'Areas containing (%s,%s)' % (x,y), areas)
    return output_json( dict( (area.id, area.as_dict() ) for area in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_point_latlon(request, lat, lon, bb=False, format=''):
    return HttpResponseRedirect("/point/4326/%s,%s%s%s" % (lon, lat, "/bb" if bb else '', '.%s' % format if format else ''))

@ratelimit(minutes=3, requests=100)
def areas_by_point_osgb(request, e, n, bb=False, format=''):
    return HttpResponseRedirect("/point/27700/%s,%s%s%s" % (e, n, "/bb" if bb else '', '.%s' % format if format else ''))

# ---

def deal_with_POST(request, call='areas'):
    url = request.POST.get('URL', '')
    if not url:
        return output_json({ 'error': 'No content specified' }, code=400)
    view, args, kwargs = resolve('/%s/%s' % (call, url))
    kwargs['request'] = request
    return view(*args, **kwargs)

# Legacy Views from old MaPit. Don't use in future.

@ratelimit(minutes=3, requests=100)
def get_voting_area_info(request, area_id):
    area = _get_voting_area_info(area_id)
    if isinstance(area, HttpResponse): return area
    return output_json(area)

def _get_voting_area_info(area_id):
    if re.match('\d\d([a-z][a-z])?([a-z][a-z])?$(?i)', area_id):
        area = get_object_or_404(Area, codes__type='ons', codes__code=area_id)
    else:
        area = get_object_or_404(Area, id=int(area_id))
    if isinstance(area, HttpResponse): return area

    try:
        os_name = area.names.get(type='O').name
    except:
        os_name = None
    try:
        ons_code = area.codes.get(type='ons').code
    except:
        ons_code = None

    current = Generation.objects.current().id
    out = {
        'area_id': area.id,
        'name': area.name,
        'os_name': os_name,
        'country': area.country,
        'parent_area_id': area.parent_area_id,
        'type': area.type,
        'ons_code': ons_code,
        'generation_low': area.generation_low_id if area.generation_low_id else 0,
        'generation_high': area.generation_high_id if area.generation_high_id else current,
        'generation': current,
    }

    for item in ('type_name', 'attend_prep', 'general_prep', 'rep_name', 'rep_name_plural',
                 'rep_name_long', 'rep_name_long_plural', 'rep_suffix', 'rep_prefix'):
        out[item] = voting_area[item].get(area.type)

    return out

@ratelimit(minutes=3, requests=100)
def get_voting_areas_info(request, area_ids):
    area_ids = area_ids.split(',')
    out = {}
    for id in area_ids:
        area = _get_voting_area_info(id)
        out[id] = {} if isinstance(area, HttpResponse) else area
    return output_json(out)

