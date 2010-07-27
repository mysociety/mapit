import re
from mapit.areas.models import Area, Generation, Geometry, Code
from mapit.shortcuts import output_json, get_object_or_404
from mapit.ratelimitcache import ratelimit
from django.contrib.gis.geos import Point
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import resolve

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
def area(request, area_id, legacy=False):
    if re.match('\d\d([A-Z]{2}|[A-Z]{4}|[A-Z]{2}\d\d\d|[A-Z]|[A-Z]\d\d)$', area_id):
        area = get_object_or_404(Area, codes__type='ons', codes__code=area_id)
    elif not re.match('\d+$', area_id):
        return output_json({ 'error': 'Bad area ID specified' }, code=400)
    else:
        area = get_object_or_404(Area, id=area_id)
    if isinstance(area, HttpResponse): return area
    return output_json( area.as_dict() )

@ratelimit(minutes=3, requests=100)
def area_polygon(request, srid, area_id, format):
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
    if srid != 27700:
        all_areas.transform(srid)
    if format=='kml': out = all_areas.kml
    elif format=='json': out = all_areas.json
    elif format=='wkt': out = all_areas.wkt
    return HttpResponse(out)
    
@ratelimit(minutes=3, requests=100)
def area_children(request, area_id, legacy=False):
    area = get_object_or_404(Area, id=area_id)
    if isinstance(area, HttpResponse): return area
    generation = Generation.objects.current()
    children = add_codes(area.children.filter(
        generation_low__lte=generation, generation_high__gte=generation
    ))
    if legacy: return output_json( [ child.id for child in children ] )
    return output_json( dict( (child.id, child.as_dict() ) for child in children ) )

@ratelimit(minutes=3, requests=100)
def area_touches(request, area_id):
    area = get_object_or_404(Area, id=area_id)
    if isinstance(area, HttpResponse): return area
    all_areas = area.polygons.all()
    if len(all_areas) > 1:
        all_areas = all_areas.collect()
    elif len(all_areas) == 1:
        all_areas = all_areas[0].polygon
    else:
        return output_json({ 'error': 'No polygons found' }, code=404)
    areas = Area.objects.filter(polygons__polygon__touches=all_areas, type=area.type)
    return output_json( dict( (a.id, a.as_dict() ) for a in areas ) )

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
def areas(request, area_ids):
    area_ids = area_ids.split(',')
    areas = add_codes(Area.objects.filter(id__in=area_ids))
    return output_json( dict( ( area.id, area.as_dict() ) for area in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_type(request, type, legacy=False):
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

    if type == 'HOC':
        HOC_AREA_ID = 900008
        areas = [ Area.objects.get(id=HOC_AREA_ID) ]
    elif min_generation == -1:
        areas = add_codes(Area.objects.filter(**args))
    else:
        args['generation_low__lte'] = generation
        args['generation_high__gte'] = min_generation
        areas = add_codes(Area.objects.filter(**args))
    if legacy: return output_json( [ a.id for a in areas ] )
    return output_json( dict( (a.id, a.as_dict() ) for a in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_name(request, name, legacy=False):
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
    return output_json(out)

@ratelimit(minutes=3, requests=100)
def area_geometry(request, area_id):
    area = _area_geometry(area_id)
    return output_json(area)

def _area_geometry(area_id):
    area = get_object_or_404(Area, id=area_id)
    if isinstance(area, HttpResponse): return area
    all_areas = area.polygons.all().collect()
    if not all_areas:
        return output_json({ 'error': 'No polygons found' }, code=404)
    out = {
        'area': all_areas.area,
        'parts': all_areas.num_geom,
        'centre_e': all_areas.centroid[0],
        'centre_n': all_areas.centroid[1],
    }
    out['min_e'], out['min_n'], out['max_e'], out['max_n'] = all_areas.extent
    all_areas.transform(4326)
    out['min_lon'], out['min_lat'], out['max_lon'], out['max_lat'] = all_areas.extent
    #all_areas.centroid.transform(4326)
    out['centre_lon'] = all_areas.centroid[0]
    out['centre_lat'] = all_areas.centroid[1]
    return out

@ratelimit(minutes=3, requests=100)
def areas_geometry(request, area_ids):
    area_ids = area_ids.split(',')
    out = dict( (id, _area_geometry(id)) for id in area_ids )
    return output_json(out)

@ratelimit(minutes=3, requests=100)
def areas_by_point(request, srid, x, y, bb=False, legacy=False):
    type = request.REQUEST.get('type', '')
    generation = request.REQUEST.get('generation', Generation.objects.current())
    if not generation: generation = Generation.objects.current()
    location = Point(float(x), float(y), srid=int(srid))
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
            args['polygons__polygon__contains'] = location
        areas = Area.objects.filter(**args)

    if legacy: return output_json( dict( (area.id, area.type) for area in areas ) )
    return output_json( dict( (area.id, area.as_dict() ) for area in areas ) )

@ratelimit(minutes=3, requests=100)
def areas_by_point_latlon(request, lat, lon, bb=False):
    return HttpResponseRedirect("/point/4326/%s,%s%s" % (lon, lat, "/bb" if bb else ''))

@ratelimit(minutes=3, requests=100)
def areas_by_point_osgb(request, e, n, bb=False):
    return HttpResponseRedirect("/point/27700/%s,%s%s" % (e, n, "/bb" if bb else ''))

# ---

def deal_with_POST(request):
    url = request.POST.get('URL', '')
    if not url:
        return output_json({ 'error': 'No content specified' }, code=400)
    view, args, kwargs = resolve('/areas/%s' % url)
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

    out = {
        'area_id': area.id,
        'name': area.name,
        'os_name': os_name,
        'country': area.country,
        'parent_area_id': area.parent_area_id,
        'type': area.type,
        'ons_code': ons_code,
        'generation_low': area.generation_low_id,
        'generation_high': area.generation_high_id,
        'generation': Generation.objects.current().id,
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
        if isinstance(area, HttpResponse): return area
        out[id] = area
    return output_json(out)

