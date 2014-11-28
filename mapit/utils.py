import re

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
