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

def check_postcode(postcode):
    postcode = re.sub('\s+', '', postcode.upper())
    if not is_valid_postcode(postcode):
        return HttpResponseBadRequest("Postcode '%s' is not valid." % postcode)
    postcode = get_object_or_404(Postcode, postcode=postcode)
    return postcode

def postcode(request, postcode, legacy=False):
    postcode = check_postcode(postcode)
    if isinstance(postcode, HttpResponseBadRequest): return postcode
    generation = request.REQUEST.get('generation', Generation.objects.current())
    areas = Area.objects.by_postcode(postcode, generation)

    # Add manual enclosing areas. 
    extra = []
    for area in areas:
        if area.type in enclosing_areas.keys():
            extra.extend(enclosing_areas[area.type])
    areas = itertools.chain(areas, Area.objects.filter(id__in=extra))
 
    if legacy:
        areas = dict( (area.type, area.id) for area in areas )
        return output_json(areas)

    out = postcode.as_dict()
    out['areas'] = dict( ( area.id, area.as_dict() ) for area in areas )
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

def example_postcode_for_area(request, area_id, legacy=False):
    area = get_object_or_404(Area, id=area_id)
    try:
        pc = Postcode.objects.filter(areas=area).order_by('?')[0]
    except:
        try:
            pc = Postcode.objects.filter(location__contained=area.polygons.all().collect()).order_by('?')[0]
        except:
            pc = None
    if pc: pc = pc.get_postcode_display()
    return output_json(pc)

# Legacy Views from old MaPit. Don't use in future.

def get_location(request, postcode, partial):
    if partial:
        return partial_postcode(request, postcode)
    postcode = check_postcode(postcode)
    if isinstance(postcode, HttpResponseBadRequest): return postcode
    return output_json(postcode.as_dict())

