import re
from mapit.areas.models import Area, Generation
from mapit.shortcuts import output_json
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
from django.http import HttpResponse

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

def area(request, area_id, legacy=False):
    area = get_object_or_404(Area, id=area_id)
    return _area(area)

def area_by_ons_code(request, ons_code):
    area = get_object_or_404(Area, code__type='ons', code__code=ons_code)
    return _area(area)

def _area(area):
    out = area.as_dict()
    return output_json(out)

def area_polygon(request, area_id, format):
    area = get_object_or_404(Area, id=area_id)
    all_areas = area.polygons.all().collect()
    if format=='kml': out = all_areas.kml
    elif format=='json': out = all_areas.json
    elif format=='wkt': out = all_areas.wkt
    return HttpResponse(out)
    
def area_children(request, area_id, legacy=False):
    area = get_object_or_404(Area, id=area_id)
    generation = Generation.objects.current()
    children = area.children.filter(
        generation_low__lte=generation, generation_high__gte=generation
    )
    if legacy: return output_json( [ child.id for child in children ] )
    return output_json( dict( (child.id, child.as_dict() ) for child in children ) )

def areas(request, area_ids):
    area_ids = area_ids.split(',')
    areas = Area.objects.filter(id__in=area_ids)
    return output_json( dict( ( area.id, area.as_dict() ) for area in areas ) )

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
        areas = Area.objects.filter(**args)
    else:
        args['generation_low__lte'] = generation
        args['generation_high__gte'] = min_generation
        areas = Area.objects.filter(**args)
    if legacy: return output_json( [ a.id for a in areas ] )
    return output_json( dict( (a.id, a.as_dict() ) for a in areas ) )

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

    areas = Area.objects.filter(**args)
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

def area_geometry(request, area_id):
    area = _area_geometry(area_id)
    return output_json(area)

def _area_geometry(area_id):
    area = get_object_or_404(Area, id=area_id)
    all_areas = area.polygons.all().collect()
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

def areas_geometry(request, area_ids):
    area_ids = area_ids.split(',')
    out = dict( (id, _area_geometry(id)) for id in area_ids )
    return output_json(out)

# OLD VIEWS

def get_voting_area_info(request, area_id):
    area = _get_voting_area_info(area_id)
    return output_json(area)

def _get_voting_area_info(area_id):
    if re.match('\d\d([a-z][a-z])?([a-z][a-z])?$(?i)', area_id):
        area = get_object_or_404(Area, code__type='ons', code__code=area_id)
    else:
        area = get_object_or_404(Area, id=int(area_id))

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

def get_voting_areas_info(request, area_ids):
    area_ids = area_ids.split(',')
    out = dict( (id, _get_voting_area_info(id)) for id in area_ids )
    return output_json(out)

def get_voting_areas_by_location(request, coordsyst, x, y, method):
    type = request.REQUEST.get('type', '')
    generation = request.REQUEST.get('generation', Generation.objects.current())

    if coordsyst == 'osgb':
        location = Point(float(x), float(y), srid=27700)
    elif coordsyst == 'wgs84':
        location = Point(float(x), float(y), srid=4326)

    args = { 'generation_low__lte': generation, 'generation_high__gte': generation }

    if ',' in type:
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type

    if method == 'box':
        args['polygons__polygon__bbcontains'] = location
    else:
        args['polygons__polygon__contains'] = location

    areas = Area.objects.filter(**args)
    out = {}
    for area in areas:
        out[area.id] = area.type

    return output_json(out)

