import re
import itertools
from mapit.postcodes.models import Postcode
from mapit.areas.models import Area, Generation
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.http import HttpResponse

def postcode(request, postcode, format='html'):
    postcode = re.sub('\s+', '', postcode.upper())
    postcode = get_object_or_404(Postcode, postcode=postcode)
    current_generation = Generation.objects.current()
    areas = []
    for area in itertools.chain(
        Area.objects.filter(
            polygon__contains=postcode.location,
            #generation_low__lte=current_generation,
            #generation_high__gte=current_generation
        ),
        postcode.areas.filter(
            #generation_low__lte=current_generation,
            #generation_high__gte=current_generation
        )
    ):
        areas.append({
            'id': area.id,
            'parent_area': area.parent_area,
            'type': area.type,
            'country': area.country,
            'generation_low': area.generation_low,
            'generation_high': area.generation_high,
            'name': area.name,
            'codes': area.all_codes,
        })

    response = HttpResponse(content_type='application/javascript; charset=utf-8')
    simplejson.dump(areas, response, ensure_ascii=False)
    return response
    
