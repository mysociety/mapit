from mapit.areas.models import Area
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.http import HttpResponse

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

