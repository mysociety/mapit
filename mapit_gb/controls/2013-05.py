# A control file for importing Boundary-Line.
# CEDs (county council electoral divisions) don't have ONS codes, so we have to
# have something manual as this is a year of county council boundary changes.
#
# The following counties have had full boundary changes (with Statutory
# Instrument number):
# - Buckinghamshire     2012/1396
# - Cumbria             2012/3113
# - Derbyshire          2012/2986
# - Gloucestershire     2012/877
# - Northamptonshire    2013/68
# - Oxfordshire         2012/1812
# - Somerset            2012/2984
# - Staffordshire       2012/875
# - Surrey              2012/1872
#
# The following have had minor changes:
# - Cambridgeshire      2012/51
# - Devon               2010/2788
# - Essex               2011/2764
# - Kent                2010/2108
# - Leicestershire      2012/2854
# - Norfolk             2012/3260 2013/220
# - North Yorkshire     2012/3150 2013/221

from mapit.models import Area

COUNTIES = [
    'Buckinghamshire', 'Cumbria', 'Derbyshire', 'Gloucestershire',
    'Northamptonshire', 'Oxfordshire', 'Somerset', 'Staffordshire', 'Surrey'
]
COUNTIES = ["%s County Council" % c for c in COUNTIES]


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""

    if type != 'CED':
        return False

    # Make sure CEDs are loaded *after* CTY
    area_within = Area.objects.filter(type__code='CTY', polygons__polygon__contains=geometry.geos.point_on_surface)[0]
    if area_within.name in COUNTIES:
        return True

    # The following have had boundary changes for the 2013 elections, but all
    # have ONS codes and so can be ignored/ detected that way:
    #
    # Anglesey          2012/2676 (W290)
    # Cornwall          2011/1
    # Durham            2012/1394
    # Northumberland    2011/2
    # Shropshire        2012/2935 (minor)

    return False
