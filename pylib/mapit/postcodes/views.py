import re
import itertools
from mapit.postcodes.models import Postcode
from mapit.postcodes.utils import is_valid_postcode, is_valid_partial_postcode
from mapit.areas.models import Area, Generation
from mapit.shortcuts import output_json
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, HttpResponseBadRequest

# Stupid fixed IDs from old MaPit
WMP_AREA_ID = 900000
EUP_AREA_ID = 900001
LAE_AREA_ID = 900002
SPA_AREA_ID = 900003
WAS_AREA_ID = 900004
NIA_AREA_ID = 900005
LAS_AREA_ID = 900006
HOL_AREA_ID = 900007
HOC_AREA_ID = 900008
enclosing_areas = {
    'LAC': [ LAE_AREA_ID, LAS_AREA_ID ],
    'SPC': [ SPA_AREA_ID ],
    'WAC': [ WAS_AREA_ID ],
    'NIE': [ NIA_AREA_ID ],
    'WMC': [ WMP_AREA_ID ],
    'EUR': [ EUP_AREA_ID ],
}

class Http400(Exception):
    pass

def _postcode(request, postcode):
    postcode = re.sub('\s+', '', postcode.upper())
    if not is_valid_postcode(postcode):
        raise Http400
    postcode = get_object_or_404(Postcode, postcode=postcode)
    generation = request.REQUEST.get('generation', Generation.objects.current())
    areas = Area.objects.by_postcode(postcode, generation)

    # Add manual enclosing areas. 
    extra = []
    for area in areas:
        if area.type in enclosing_areas.keys():
            extra.extend(enclosing_areas[area.type])
    areas = itertools.chain(areas, Area.objects.filter(id__in=extra))
 
    return areas, postcode
    
def postcode(request, postcode):
    try:
        lookup, postcode = _postcode(request, postcode)
    except Http400:
        return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
    areas = []
    for area in lookup:
        areas.append({
            'id': area.id,
            'name': area.name,
            'parent_area': area.parent_area_id,
            'type': (area.type, area.get_type_display()),
            'country': (area.country, area.get_country_display()),
            'generation_low': area.generation_low_id,
            'generation_high': area.generation_high_id,
            'codes': area.all_codes,
        })
    out = {
        'longitude': postcode.location[0]
        'latitude': postcode.location[1]
        'areas': areas,
    }
    if postcode.postcode[0:2] == 'BT':
        postcode.location.transform(29902)
        out['coordsyst'] = 'I'
    else:
        loc.transform(27700)
        out['coordsyst'] = 'G'
    out['easting'] = postcode.location[0]
    out['northing'] = postcode.location[1]

    return output_json(out)
    
# OLD VIEWS

def get_voting_areas(request, postcode):
    try:
        lookup, postcode = _postcode(request, postcode)
    except Http400:
        return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
    areas = {}
    for area in lookup:
        areas[area.type] = area.id
    return output_json(areas)

def get_example_postcode(request, area_id):
    area = get_object_or_404(Area, id=area_id)
    try:
        pc = Postcode.objects.filter(areas=area)[0]
    except:
        try:
            pc = Postcode.objects.filter(location__contained=area.polygons.all().collect()).order_by('?')[0]
        except:
            pc = None
    return HttpResponse(pc)

def get_location(request, postcode, partial):
    postcode = re.sub('\s+', '', postcode.upper())
    irish = (postcode[0:2] == 'BT')

    if partial:
        if is_valid_postcode(postcode):
            postcode = re.sub('\d[A-Z]{2}$', '', postcode)
        if not is_valid_partial_postcode(postcode):
            return HttpResponseBadRequest("Partial postcode '%s' is not valid." % postcode)
        try:
            loc = Postcode.objects.filter(postcode__startswith=postcode).collect().centroid
        except:
            raise Http404
    else:
        if not is_valid_postcode(postcode):
            return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
        try:
            loc = Postcode.objects.get(postcode=postcode).location
        except Postcode.DoesNotExist:
            raise Http404

    result = {}
    result['wgs84_lon'] = loc[0]
    result['wgs84_lat'] = loc[1]
    if irish:
        loc.transform(29902)
        result['coordsyst'] = 'I'
    else:
        loc.transform(27700)
        result['coordsyst'] = 'G'
    result['easting'] = loc[0]
    result['northing'] = loc[1]

    return output_json(result)
