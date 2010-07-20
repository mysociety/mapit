import re
import itertools
from mapit.postcodes.models import Postcode
from mapit.postcodes.utils import is_valid_postcode, is_valid_partial_postcode
from mapit.areas.models import Area, Generation
from mapit.shortcuts import output_json
from django.shortcuts import get_object_or_404
from django.http import HttpResponseBadRequest, Http404

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
        areas.append(area.as_dict())
    out = postcode.as_dict()
    out['areas'] = areas
    return output_json(out)
    
def partial_postcode(request, postcode):
    postcode = re.sub('\s+', '', postcode.upper())
    if is_valid_postcode(postcode):
        postcode = re.sub('\d[A-Z]{2}$', '', postcode)
    if not is_valid_partial_postcode(postcode):
        return HttpResponseBadRequest("Partial postcode '%s' is not valid." % postcode)
    try:
        postcode = Postcode(
            postcode = 'temp',
            location = Postcode.objects.filter(postcode__startswith=postcode).collect().centroid
        )
    except:
        raise Http404
    return output_json(postcode.as_dict())

def example_postcode_for_area(request, area_id):
    area = get_object_or_404(Area, id=area_id)
    try:
        pc = Postcode.objects.filter(areas=area).order_by('?')[0]
    except:
        try:
            pc = Postcode.objects.filter(location__contained=area.polygons.all().collect()).order_by('?')[0]
        except:
            pc = None
    return output_json(pc)

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
    return example_postcode_for_area(request, area_id)

def get_location(request, postcode, partial):
    postcode = re.sub('\s+', '', postcode.upper())
    if partial:
        return partial_postcode(request, postcode)
    else:
        if not is_valid_postcode(postcode):
            return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
        postcode = get_object_or_404(Postcode, postcode=postcode)

    return output_json(postcode.as_dict())

