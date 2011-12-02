import re
from django.conf import settings

def is_valid_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    if settings.MAPIT_COUNTRY == 'GB':
        return is_valid_uk_postcode(pc)
    elif settings.MAPIT_COUNTRY == 'NO':
        return is_valid_no_postcode(pc)
    return False

def is_special_uk_postcode(pc):
    if pc in (
        'ASCN1ZZ', # Ascension Island
        'BBND1ZZ', # BIOT
        'BIQQ1ZZ', # British Antarctic Territory
        'FIQQ1ZZ', # Falkland Islands
        'PCRN1ZZ', # Pitcairn Islands
        'SIQQ1ZZ', # South Georgia and the South Sandwich Islands
        'STHL1ZZ', # St Helena
        'TDCU1ZZ', # Tristan da Cunha
        'TKCA1ZZ', # Turks and Caicos Islands
        'GIR0AA', 'G1R0AA', # Girobank
        'SANTA1', # Santa Claus
    ):
        return True
    return False

def is_valid_uk_postcode(pc):
    # Our test postcode
    if pc in ('ZZ99ZZ', 'ZZ99ZY'): return True

    if is_special_uk_postcode(pc): return True

    # See http://www.govtalk.gov.uk/gdsc/html/noframes/PostCode-2-1-Release.htm
    inward = 'ABDEFGHJLNPQRSTUWXYZ'
    fst = 'ABCDEFGHIJKLMNOPRSTUWYZ'
    sec = 'ABCDEFGHJKLMNOPQRSTUVWXY'
    thd = 'ABCDEFGHJKSTUW'
    fth = 'ABEHMNPRVWXY'

    if re.match('[%s][1-9]\d[%s][%s]$' % (fst, inward, inward), pc) or \
        re.match('[%s][1-9]\d\d[%s][%s]$' % (fst, inward, inward), pc) or \
        re.match('[%s][%s]\d\d[%s][%s]$' % (fst, sec, inward, inward), pc) or \
        re.match('[%s][%s][1-9]\d\d[%s][%s]$' % (fst, sec, inward, inward), pc) or \
        re.match('[%s][1-9][%s]\d[%s][%s]$' % (fst, thd, inward, inward), pc) or \
        re.match('[%s][%s][1-9][%s]\d[%s][%s]$' % (fst, sec, fth, inward, inward), pc):
        return True

    return False

# Norwegian postcodes are four digits. Some put "no-" in front, but
# this is ignored here.
def is_valid_no_postcode(pc):
    if re.match('\d{4}$', pc):
        return True
    return False

def is_valid_partial_postcode(pc):
    pc = re.sub('\s+', '', pc.upper())

    if settings.MAPIT_COUNTRY == 'GB':
        return is_valid_partial_uk_postcode(pc)
    elif settings.MAPIT_COUNTRY == 'NO':
        return is_valid_partial_no_postcode(pc)
    return False

def is_valid_partial_uk_postcode(pc):
    # Our test postcode
    if pc == 'ZZ9': return True
    
    # See http://www.govtalk.gov.uk/gdsc/html/noframes/PostCode-2-1-Release.htm
    fst = 'ABCDEFGHIJKLMNOPRSTUWYZ'
    sec = 'ABCDEFGHJKLMNOPQRSTUVWXY'
    thd = 'ABCDEFGHJKSTUW'
    fth = 'ABEHMNPRVWXY'
  
    if re.match('[%s][1-9]$' % (fst), pc) or \
        re.match('[%s][1-9]\d$' % (fst), pc) or \
        re.match('[%s][%s]\d$' % (fst, sec), pc) or \
        re.match('[%s][%s][1-9]\d$' % (fst, sec), pc) or \
        re.match('[%s][1-9][%s]$' % (fst, thd), pc) or \
        re.match('[%s][%s][1-9][%s]$' % (fst, sec, fth), pc):
        return True

    return False

# Should match one, two and three digits.
def is_valid_partial_no_postcode(pc):
    if re.match('\d{1,3}$', pc):
        return True
    return False

