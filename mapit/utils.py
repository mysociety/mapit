import re
from django.conf import settings

from mapit import countries

def is_valid_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    if hasattr(countries, 'is_valid_postcode'):
        return countries.is_valid_postcode(pc)
    return False

def is_valid_partial_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    if hasattr(countries, 'is_valid_partial_postcode'):
        return countries.is_valid_partial_postcode(pc)
    return False

def sorted_areas(areas):
    if hasattr(countries, 'sorted_areas'):
        return countries.sorted_areas(areas)
    return list(areas)
