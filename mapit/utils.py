import re

from mapit import countries


re_number = r'[+-]?(?:\d*\.)?\d+'


def is_valid_postcode(pc):
    pc = re.sub(r'\s+', '', pc.upper())

    if hasattr(countries, 'is_valid_postcode'):
        return countries.is_valid_postcode(pc)
    return False


def is_valid_partial_postcode(pc):
    pc = re.sub(r'\s+', '', pc.upper())

    if hasattr(countries, 'is_valid_partial_postcode'):
        return countries.is_valid_partial_postcode(pc)
    return False
