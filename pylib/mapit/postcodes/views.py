import re
import itertools
from mapit.postcodes.models import Postcode
from mapit.postcodes.utils import is_valid_postcode, is_valid_partial_postcode
from mapit.areas.models import Area, Generation
from django.shortcuts import get_object_or_404
from django.utils import simplejson
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

    # Add fictional enclosing areas. 
    extra = []
    for area in areas:
        if area.type in enclosing_areas.keys():
            extra.extend(enclosing_areas[area.type])
    areas = itertools.chain(araes, Area.objects.filter(id__in=extra))
 
    return areas
    
def postcode(request, postcode, format='html'):
    try:
        lookup = _postcode(request, postcode)
    except Http400:
        return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
    areas = {}
    for area in lookup:
        areas.append({
            'id': area.id,
            'name': area.name,
            'parent_area': area.parent_area.id if area.parent_area else None,
            'type': (area.type, area.get_type_display()),
            'country': (area.country, area.get_country_display()),
            'generation_low': area.generation_low.id,
            'generation_high': area.generation_high.id,
            'codes': area.all_codes,
        })
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(areas, response, ensure_ascii=False)
    return response
    
# OLD VIEWS

def get_voting_areas(request):
    postcode = request.REQUEST['postcode']
    try:
        lookup = _postcode(request, postcode)
    except Http400:
        return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
    areas = {}
    for area in lookup:
        areas[area.type] = area.id
    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(areas, response, ensure_ascii=False)
    return response

def get_example_postcode(request, area_id):
    area = get_object_or_404(Area, id=area_id)
    pc = Postcode.objects.filter(areas=area)[0]
    if not pc:
        pc = Postcode.objects.filter(location__contained=area.polygons.all().collect()).order_by('?')[0]
    return HttpResponse(pc)

def get_location(request):
    postcode = re.sub('\s+', '', request.REQUEST.get('postcode', '')).upper()
    try:
        partial = int(request.REQUEST['partial'])
    except:
        partial = 0
    irish = (postcode[0:2] == 'BT')

    if not postcode:
        return HttpResponseBadRequest("Postcode must be given.")

    result = {}
    if re.match('ZZ9', postcode): return result
    if partial:
        if is_valid_postcode(postcode):
            postcode = re.sub('\d[A-Z]{2}$', '', postcode)
        if not is_valid_partial_postcode(postcode):
            return HttpResponseBadRequest("Partial postcode '%s' is not valid." % postcode)
        loc = Postcode.objects.filter(postcode__startswith=postcode).collect().centroid()
    else:
        if not is_valid_postcode(postcode):
            return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
        try:
            postcode = Postcode.objects.get(postcode=postcode)
        except Postcode.DoesNotExist:
            raise Http404
        loc = postcode.location

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

    return result
