import re
from mapit.postcodes.models import Postcode
from mapit.areas.models import Area
from django.shortcuts import get_object_or_404
from django.core import serializers
from django.http import HttpResponse

def postcode(request, postcode, format='html'):
    postcode = re.sub('\s+', '', postcode.upper())
    postcode = get_object_or_404(Postcode, postcode=postcode)
    postcode_within = Area.objects.filter(polygon__contains=postcode.location)
    postcode_within.extend(postcode.areas)

    response = HttpResponse(content_type='application/javascript; charset=utf-8')

    json = serializers.get_serializer('json')()
    json.serialize(postcode_within, ensure_ascii=False, stream=response)
    return response
    
