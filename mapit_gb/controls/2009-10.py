# A control file for importing Boundary-Line.
# Not all areas have ONS codes, so we have to have something
# manual to e.g. tell us if some WMC have changed.
#
# Things without ONS codes: CED EUR GLA LAC SPC SPE WAC WAE WMC
#
# For Oct 2009, it doesn't matter what this returns, as it's
# the first Open version and the database will/should be empty.
#
# This edition of Boundary-Line uses the old SNAC codes


def code_version():
    return 'ons'


def check(name, type, country, geometry):
    """Should return True if this area is NEW, False if we should match"""
    return False
