import re

from django.core.urlresolvers import reverse, NoReverseMatch
from django.http import HttpResponseRedirect
from ukpostcodeutils import validation

from mapit.shortcuts import get_object_or_404


def area_code_lookup(request, area_code, format):
    from mapit.models import Area, CodeType
    area_code_type = None
    if re.match('\d\d([A-Z]{2}|[A-Z]{4}|[A-Z]{2}\d\d\d|[A-Z]|[A-Z]\d\d)$', area_code):
        area_code_type = CodeType.objects.get(code='ons')
    elif re.match('[EW]0[12]\d{6}$', area_code):  # LSOA/MSOA have ONS code type
        area_code_type = CodeType.objects.get(code='ons')
    elif re.match('[ENSW]\d{8}$', area_code):
        area_code_type = CodeType.objects.get(code='gss')
    if not area_code_type:
        return None

    args = {'format': format, 'codes__type': area_code_type, 'codes__code': area_code}
    if re.match('[EW]01', area_code):
        args['type__code'] = 'OLF'
    elif re.match('[EW]02', area_code):
        args['type__code'] = 'OMF'

    area = get_object_or_404(Area, **args)
    area_kwargs = {'area_id': area.id}
    if format:
        area_kwargs['format'] = format
    # We're called either by area or area_polygon
    try:
        redirect_path = reverse('area', kwargs=area_kwargs)
    except NoReverseMatch:
        redirect_path = reverse('area_polygon', kwargs=area_kwargs)
    # If there was a query string, make sure it's passed on in the
    # redirect:
    if request.META['QUERY_STRING']:
        redirect_path += "?" + request.META['QUERY_STRING']
    return HttpResponseRedirect(redirect_path)


def canonical_postcode(pc):
    pc = re.sub('[^A-Z0-9]', '', pc.upper())
    return pc


SPECIAL_POSTCODES = (
    'ASCN1ZZ',  # Ascension Island
    'BBND1ZZ',  # BIOT
    'BIQQ1ZZ',  # British Antarctic Territory
    'FIQQ1ZZ',  # Falkland Islands
    'PCRN1ZZ',  # Pitcairn Islands
    'SIQQ1ZZ',  # South Georgia and the South Sandwich Islands
    'STHL1ZZ',  # St Helena
    'TDCU1ZZ',  # Tristan da Cunha
    'TKCA1ZZ',  # Turks and Caicos Islands
    'GIR0AA', 'G1R0AA',  # Girobank
    'SANTA1', 'XM45HQ',  # Santa Claus
)


def is_special_postcode(pc):
    return pc in SPECIAL_POSTCODES


def is_valid_postcode(pc):
    return validation.is_valid_postcode(pc, SPECIAL_POSTCODES + ('ZZ99ZZ', 'ZZ99ZY'))


def is_valid_partial_postcode(pc):
    return validation.is_valid_partial_postcode(pc, ('ZZ9',))


def get_postcode_display(pc):
    return re.sub('([0-9]..)$', r' \1', pc).strip()


def augment_postcode(postcode, result):
    pc = postcode.postcode
    if is_special_postcode(pc):
        return
    if pc[0:2] == 'BT':
        loc = postcode.as_irish_grid()
        result['coordsyst'] = 'I'
    else:
        loc = postcode.location
        loc.transform(27700)
        result['coordsyst'] = 'G'
    result['easting'] = int(round(loc[0]))
    result['northing'] = int(round(loc[1]))


# Hacky function to restrict certain geographical links in the HTML pages to
# types to make them more likely to return results.
def restrict_geo_html(area):
    geotype = {}
    if area.type.code == 'EUR':
        geotype = {'touches': ['EUR'], 'overlaps': ['UTA'], 'covers': ['UTA'], 'coverlaps': ['UTA']}
    elif area.type.code in ('CTY', 'UTA'):
        geotype = {
            'touches': ['CTY', 'DIS', 'MTD', 'LBO', 'COI', 'UTA'],
            'overlaps': ['WMC'],
            'covers': ['CED', 'DIW', 'MTW', 'LBW', 'UTE', 'UTW'],
            'coverlaps': ['CED', 'DIW', 'MTW', 'LBW', 'UTE', 'UTW']}
    elif area.type.code == 'COI':
        geotype = {'covers': ['CPC'], 'coverlaps': ['CPC']}
    elif area.type.code == 'LGD':
        geotype = {'overlaps': ['LGE', 'LGW'], 'coverlaps': ['LGE', 'LGW']}
    elif area.type.code == 'GLA':
        geotype = {'touches': ['CTY', 'UTA'], 'overlaps': ['WMC'], 'covers': ['LBO'], 'coverlaps': ['WMC']}
    elif area.type.code == 'SPE':
        geotype = {'touches': ['SPE'], 'overlaps': ['UTA'], 'covers': ['UTA'], 'coverlaps': ['UTA']}
    elif area.type.code == 'WAE':
        geotype = {'touches': ['WAE'], 'overlaps': ['UTA'], 'covers': ['UTA'], 'coverlaps': ['UTA']}
    for k, v in geotype.items():
        geotype[k] = ['?type=%s' % ','.join(v), ' (%s)' % ', '.join(v)]
    return geotype


def make_friendly_name(name_obj, name):
    n = re.sub('\s+', ' ', name.name.strip())
    n = n.replace('St. ', 'St ')
    if name.type.code == 'M':
        return n
    if name.type.code == 'S':
        return n
    # Type must be 'O' here
    n = re.sub(' Euro Region$', '', n)  # EUR
    n = re.sub(' (Burgh|Co|Boro) Const$', '', n)  # WMC
    n = re.sub(' P Const$', '', n)  # SPC
    n = re.sub(' PER$', '', n)  # SPE
    n = re.sub(' GL Assembly Const$', '', n)  # LAC
    n = re.sub(' Assembly Const$', '', n)  # WAC
    n = re.sub(' Assembly ER$', '', n)  # WAE
    n = re.sub(' London Boro$', ' Borough', n)  # LBO
    if name_obj.area.country and name_obj.area.country.name == 'Wales':
        n = re.sub('^.*? - ', '', n)  # UTA
    n = re.sub('(?:The )?City of (.*?) (District )?\(B\)$', r'\1 City', n)  # UTA
    n = re.sub(' District \(B\)$', ' Borough', n)  # DIS
    n = re.sub(' \(B\)$', ' Borough', n)  # DIS
    if name_obj.area.type.code in ('CTY', 'DIS', 'LBO', 'UTA', 'MTD'):
        n += ' Council'
    n = re.sub(' (ED|CP)$', '', n)  # CPC, CED, UTE
    n = re.sub(' Ward$', '', n)  # DIW, LBW, MTW, UTW
    return n


def name_save_hook(name_obj):
    name = name_obj.area.names.filter(type__code__in=('M', 'O', 'S')).order_by('type__code')[:1]
    if name:
        name_obj.area.name = make_friendly_name(name_obj, name[0])
        name_obj.area.save()
