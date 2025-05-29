# A control file for importing October 2015 Boundary-Line.

# This control file assumes previous Boundary-Lines have been imported,
# because it uses that information. If this is a first import, use the
# first-gss control file.

from mapit.models import Area, Generation


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    if type in ('WAC', 'WAE'):
        # The May 2016+ boundaries have been given in Boundary-Line since
        # October 2013. This was fixed for the October 2015 edition, by putting
        # the old boundaries back, so we need to rejig things somehow. Easiest
        # to put them in as new boundaries (even though they'll be same as old
        # ones), but we'll have to remove the ONS code from the old ones so
        # there aren't multiple results
        a = Area.objects.get(codes__type__code='gss', codes__code=ons_code)
        a.codes.filter(type__code='gss').delete()
        return True

    if type == 'CPC' and name == 'Wareham Town CP':
        # Appeared in October 2013 edition with wrong ID, then both 201i4
        # editions with right ID, then disappeared in May 2015 edition...
        a = Area.objects.get(codes__type__code='gss', codes__code='E04012327')
        a.generation_high = Generation.objects.current()
        return a

    # This is the default
    return False
