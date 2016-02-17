# A control file for importing Boundary-Line.
# Not all areas have ONS codes, so we have to have something
# manual to e.g. tell us if some WMC have changed.
#
# Things without ONS codes: CED EUR GLA LAC SPC SPE WAC WAE WMC
#
# This edition of Boundary-Line uses the new SNAC codes


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""

    return False
