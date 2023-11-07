# A control file for importing October 2023 Boundary-Line.

# This control file assumes previous Boundary-Lines have been imported,
# because it uses that information. If this is a first import, use the
# first-gss control file.

from mapit.models import Area, Generation


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    if type == 'CPC' and name == 'Hargrave CP' and ons_code == 'E04009317':
        # In May 2023 Hargrave CP was given the GSS ID that should have been
        # given to Ousden. So it is not in the current generation and isn't
        # found, and we have to help it along
        a = Area.objects.get(codes__type__code='gss', codes__code='E04009317')
        a.generation_high = Generation.objects.current()
        return a

    # This is the default
    return False
