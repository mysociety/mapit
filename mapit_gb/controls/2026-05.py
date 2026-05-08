# A control file for importing Boundary-Line.
# CEDs (county council electoral divisions) don't have ONS codes, so we have to
# have something manual as this is a year of county council boundary changes.
#
# OS release notes are at
# https://docs.os.uk/os-downloads/products/areas-and-zones-portfolio/boundary-line/release-notes/may-2026
#
# The following English counties have had full boundary changes:
# Essex, Norfolk, Suffolk.
# Unitaries with boundary changes are the following, but we spot them
# automatically by GSS code: Milton Keynes, Swindon, Thurrock.
# And lots of MTDs as well.

from mapit.models import Area, Generation

COUNTIES_CHANGED = ["%s County Council" % c for c in [
    'Essex', 'Norfolk', 'Suffolk'
]]
COUNTIES_NOT_CHANGED = ["%s County Council" % c for c in [
    'Cambridgeshire', 'Derbyshire', 'Devon', 'Dorset', 'East Sussex',
    'Gloucestershire', 'Hampshire', 'Hertfordshire', 'Kent', 'Lancashire',
    'Leicestershire', 'Lincolnshire', 'Oxfordshire', "Northamptonshire",
    "North Yorkshire", 'Nottinghamshire', "Somerset", 'Staffordshire',
    "Surrey", 'Warwickshire', 'West Sussex', 'Worcestershire'
]]


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS/unit_id code, or an Area to be used as an override instead."""

    current = Generation.objects.current()
    if not current:  # Fresh import
        return False

    # We already have ONS codes in our system for the Welsh Parliament,
    # and we want these to go in as new entries
    if type == 'WAC':
        return True

    # Some UTAs have had boundary changes, but have ONS codes and so can be
    # ignored/ detected that way.
    if type != 'CED':
        return False

    # Make sure CEDs are loaded *after* CTY
    area_within = Area.objects.filter(type__code='CTY', polygons__polygon__contains=geometry.geos.point_on_surface)[0]
    if area_within.name in COUNTIES_CHANGED:
        return True
    elif area_within.name in COUNTIES_NOT_CHANGED:
        return False
    raise Exception("Bad county name given: %s" % area_within.name)
