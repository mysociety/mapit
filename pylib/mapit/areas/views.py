import re
from mapit.areas.models import Area, Generation
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.http import HttpResponse, HttpResponseBadRequest

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

def area(request, area_id, format='html'):
    area = get_object_or_404(Area, id=area_id)
    out = {
        'id': area.id,
        'name': area.name,
        'parent_area': area.parent_area.id if area.parent_area else None,
        'type': (area.type, area.get_type_display()),
        'country': (area.country, area.get_country_display()),
        'generation_low': area.generation_low.id,
        'generation_high': area.generation_high.id,
        'codes': area.all_codes,
    }
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(out, response, ensure_ascii=False)
    return response

# OLD VIEWS

def get_voting_area_info(request):
    try:
        area_id = request.REQUEST['id']
    except:
        return HttpResponseBadRequest("Bad area ID given")
    area = _get_voting_area_info(area_id)
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(area, response, ensure_ascii=False)
    return response

def _get_voting_area_info(area_id):
    if re.match('\d\d([a-z][a-z])?([a-z][a-z])?$(?i)', area_id):
        area = get_object_or_404(Area, code__type='ons', code__code=area_id)
    else:
        area = get_object_or_404(Area, id=int(area_id))

    try:
        os_name = area.names.get(type='O')
    except:
        os_name = ''
    try:
        ons_code = area.codes.get(type='ons')
    except:
        ons_code = ''

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
        'generation': Generation.objects.current(),
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
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(out, response, ensure_ascii=False)
    return response

