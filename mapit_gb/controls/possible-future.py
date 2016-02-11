# A control file for importing Boundary-Line.
# CEDs don't have ONS codes, so we have to have something manual
# to e.g. tell us if some county council wards have changed.
#
# In the future, a county council (CTY) may have boundary changes to its
# electoral divisions (CED). It's the only one that's tricky, as the others
# will all change at once, but not all CEDs will be changing.
#
# In this example, Buckinghamshire County Council has had boundary changes.
#
# This edition of Boundary-Line uses the new SNAC codes

import re

from mapit.models import Area


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""

    if type != 'CED':
        return False

    # Make sure CEDs are loaded *after* CTY
    area_within = Area.objects.filter(type__code='CTY', polygons__polygon__contains=geometry.geos.point_on_surface)[0]
    if re.search('Buckinghamshire(?i)', area_within.name):
        return True

    return False
