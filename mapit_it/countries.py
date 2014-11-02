import re
__author__ = 'guglielmo'

# SRID to also output area geometry information in
area_geometry_srid = 32632


# Italian postcodes are five digits.
def is_valid_postcode(pc):
    if re.match('\d{5}$', pc):
        return True
    return False
