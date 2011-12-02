import re
from django.conf import settings

import mapit.countries

def is_valid_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    if hasattr(mapit.countries, 'is_valid_postcode'):
        return mapit.countries.is_valid_postcode(pc)
    return False

def is_valid_partial_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    if hasattr(mapit.countries, 'is_valid_partial_postcode'):
        return mapit.countries.is_valid_partial_postcode(pc)
    return False

