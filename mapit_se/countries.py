import re

# SRID to also output area geometry information in
# area_geometry_srid = 32633 # Norway's used srid
area_geometry_srid = 30800  # found here:
# http://postgis.refractions.net/pipermail/postgis-users/2003-March/002207.html


# Swedish postcodes are five digits, with a possible space before the last two.
# Some put "se-" in front, but this is ignored here.
def is_valid_postcode(pc):
    if re.match('\d{3}\s*\d{2}$', pc):
        return True
    return False


# Should match one, two and three digits.
def is_valid_partial_postcode(pc):
    if re.match('\d{1,3}$', pc):
        return True
    return False
