# A control file for importing Boundary-Line.
# Not all areas have ONS codes, so we have to have something
# manual to e.g. tell us if some WMC have changed.
#
# Things without ONS codes: CED EUR GLA LAC SPC SPE WAC WAE WMC
#
# For May 2010, England and Wales WMC are all new. I think that's it!
#
# This edition of Boundary-Line uses the old SNAC codes


def code_version():
    return 'ons'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""
    if type == 'WMC' and country in ('E', 'W'):
        return True
    return False
