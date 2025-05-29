# A control file for importing October 2020 Boundary-Line.

import re
from mapit.models import Area, CodeType


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    # The GLA area now has a GSS code, we should
    # match it up with the existing area.
    if type == 'GLA':
        try:
            area = Area.objects.get(type__code='GLA')
            area.codes.update_or_create(type=CodeType.objects.get(code='gss'), defaults={'code': ons_code})
            return area
        except Area.DoesNotExist:
            pass

    # Boundary-Line has decided to continue the Buckinghamshire county/district
    # ward boundaries but remove the councils. If we have run the script that
    # created the Buckinghamshire UTA and UTWs, make sure we allow these in as
    # new boundaries (though they'll be the same as old ones). We have to
    # remove the ONS code from the old ones so there aren't multiple results.
    if type in ('DIW', 'CED'):
        try:
            area_within = Area.objects.get(
                type__code='UTA', polygons__polygon__contains=geometry.geos.point_on_surface)
            if re.search('Buckinghamshire(?i)', area_within.name):
                if ons_code:
                    a = Area.objects.get(codes__type__code='gss', codes__code=ons_code)
                    if commit:
                        a.codes.filter(type__code='gss').delete()
                return True
        except Area.DoesNotExist:
            pass

    return False
