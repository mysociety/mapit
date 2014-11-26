import re

# SRID to also output area geometry information in
area_geometry_srid = 32633


# Norwegian postcodes are four digits. Some put "no-" in front, but
# this is ignored here.
def is_valid_postcode(pc):
    if re.match('\d{4}$', pc):
        return True
    return False


# Should match one, two and three digits.
def is_valid_partial_postcode(pc):
    if re.match('\d{1,3}$', pc):
        return True
    return False
