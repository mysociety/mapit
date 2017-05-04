# A control file for importing Boundary-Line.
# CEDs (county council electoral divisions) don't have ONS codes, so we have to
# have something manual as this is a year of county council boundary changes.
#
# The following English counties have had full boundary changes:
# - Cambridgeshire 2016/1222
# - Devon 2016/657
# - Dorset 2016/64
# - East Sussex 2016/1225
# - Hampshire 2016/1223
# - Hertfordshire 2015/1873
# - Kent 2016/658
# - Lancashire 2016/1069
# - Leicestershire 2016/1070
# - Lincolnshire 2016/1226
# - Nottinghamshire 2016/659
# - Warwickshire 2015/1874
# - West Sussex 2016/1224

# The following have had minor changes:
# - Gloucestershire 2017/82 (Cotswold)
# - Kent 2017/117 (Ashford)
# - Northamptonshire 2015/563 (East Northamptonshire) 2016/857 (Kettering)
# - Oxfordshire 2017/119 (Cherwell) 2017/128 (Vale of White Horse) 2017/129 (South Oxfordshire)
# - Suffolk 2017/118 (St Edmundsbury)

from mapit.models import Area

COUNTIES_CHANGED = ["%s County Council" % c for c in [
    'Cambridgeshire', 'Devon', 'Dorset', 'East Sussex', 'Hampshire',
    'Hertfordshire', 'Kent', 'Lancashire', 'Leicestershire', 'Lincolnshire',
    'Nottinghamshire', 'Warwickshire', 'West Sussex'
]]
COUNTIES_NOT_CHANGED = ["%s County Council" % c for c in [
    "Buckinghamshire", "Cumbria", "Derbyshire", "Essex", "Gloucestershire",
    "Norfolk", "Northamptonshire", "North Yorkshire", "Oxfordshire",
    "Somerset", "Staffordshire", "Suffolk", "Surrey", "Worcestershire"
]]


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""

    # Scottish councils have had boundary changes, and a few minor
    # alterations to Welsh ones (2016/ 1151, 1155, 1156, 1158) but
    # have ONS codes and so can be ignored/ detected that way.

    if type != 'CED':
        return False

    # Make sure CEDs are loaded *after* CTY
    area_within = Area.objects.filter(type__code='CTY', polygons__polygon__contains=geometry.geos.point_on_surface)[0]
    if area_within.name in COUNTIES_CHANGED:
        return True
    elif area_within.name in COUNTIES_NOT_CHANGED:
        return False
    raise Exception("Bad county name given: %s" % area_within.name)
