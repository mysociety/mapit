# A control file for importing May 2022 Boundary-Line.

# This control file assumes previous Boundary-Lines have been imported,
# because it uses that information. If this is a first import, use the
# first-gss control file.

from mapit.models import Area, Generation


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    missing_parishes = {
        'Wexham Court CP': 'E04001211',
        'Britwell CP': 'E04012334',
    }
    if type == 'CPC' and name in missing_parishes.keys():
        # Missing in previous editions
        a = Area.objects.get(codes__type__code='gss', codes__code=missing_parishes[name])
        a.generation_high = Generation.objects.current()
        return a

    # This is the default
    return False
