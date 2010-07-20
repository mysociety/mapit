import re
from mapit.areas.models import Area, Generation
from mapit.shortcuts import output_json
from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest

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
        'LBO':  "on the",
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

def area(request, area_id):
    area = get_object_or_404(Area, id=area_id)
    out = {
        'id': area.id,
        'name': area.name,
        'parent_area': area.parent_area_id,
        'type': (area.type, area.get_type_display()),
        'country': (area.country, area.get_country_display()),
        'generation_low': area.generation_low_id,
        'generation_high': area.generation_high_id,
        'codes': area.all_codes,
    }
    return output_json(out)

# OLD VIEWS

def get_voting_area_info(request):
    try:
        area_id = request.REQUEST['id']
    except:
        return HttpResponseBadRequest("Bad area ID given")
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

def get_voting_areas_info(request):
    try:
        area_ids = request.REQUEST['ids'].split(',')
    except:
        return HttpResponseBadRequest("Bad area ID given")

    out = dict( (id, _get_voting_area_info(id)) for id in area_ids )
    return output_json(out)

def get_voting_areas_by_location(request):
    try:
        method = request.REQUEST['method']
        assert method in ('box', 'polygon')
    except:
        return HttpResponseBadRequest("Method must be given, and be box or polygon")

    type = request.REQUEST.get('type', '')
    generation = request.REQUEST.get('generation', Generation.objects.current())

    try:
        easting = request.REQUEST['e']
        northing = request.REQUEST['n']
        location = Point(float(easting), float(northing), srid=27700)
    except:
        try:
            lat = request.REQUEST['lat']
            lon = request.REQUEST['lon']
            location = Point(float(lon), float(lat), srid=4326)
        except:
            return HttpResponseBadRequest("Co-ordinates must be supplied")

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

def get_voting_area_geometry(request):
    try:
        area_id = request.REQUEST['id']
    except:
        return HttpResponseBadRequest("Bad area ID given")
    area = _get_voting_area_geometry(area_id)
    return output_json(area)

def _get_voting_area_geometry(area_id):
    polygon_type = request.REQUEST.get('polygon_type')
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
    if polygon_type:
        out['polygon'] = all_areas.json
    return output_json(out)

def get_voting_areas_geometry(request):
    try:
        area_ids = request.REQUEST['ids'].split(',')
    except:
        return HttpResponseBadRequest("Bad area IDs given")

    out = dict( (id, _get_voting_area_geometry(id)) for id in area_ids )
    return output_json(out)

def get_voting_area_children(request):
    try:
        area_id = request.REQUEST['id']
    except:
        return HttpResponseBadRequest("Bad area ID given")
    area = get_object_or_404(Area, id=area_id)
    generation = Generation.objects.current()
    children = Area.objects.filter(parent_area=area,
        generation_low__lte=generation, generation_high__gte=generation
    )
    out = [ child.id for child in children ]
    return output_json(out)

def get_areas_by_type(request):
    try:
        min_generation = int(request.REQUEST['min_generation'])
    except:
        min_generation = 0

    type = request.REQUEST.get('type', '')
    if not type:
        return HttpResponseBadRequest('Please specify type')

    args = {}
    if ',' in type:
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type

    if type == 'HOC':
        HOC_AREA_ID = 900008
        out = [ Area.objects.get(id=HOC_AREA_ID) ]
    elif min_generation == -1:
        out = Area.objects.filter(**args)
    else:
        generation = Generation.objects.current()
        if not generation: min_generation = generation
        args['generation_low__lte'] = generation
        args['generation_high__gte'] = min_generation
        out = Area.objects.filter(**args)
    out = [ a.id for a in out ]
    return output_json(out)

def get_voting_area_by_name(request):
    try:
        min_generation = int(request.REQUEST['min_generation'])
    except:
        min_generation = 0
    generation = Generation.objects.current()

    name = request.REQUEST.get('name')
    if not name:
        return HttpResponseBadRequest('Please specify name')

    type = request.REQUEST.get('type', '')

    args = {
        'name__icontains': name,
        'generation_low__lte': generation,
        'generation_high__gte': min_generation,
    }
    if ',' in type:
        args['type__in'] = type.split(',')
    elif type:
        args['type'] = type

    areas = Area.objects.filter(**args)
    out = {}
    for area in areas:
        out[area.id] = {
            'area_id': area.id,
            'name': area.name,
            'type': area.type,
            'parent_area_id': area.parent_area_id,
        }

    return output_json(out)

