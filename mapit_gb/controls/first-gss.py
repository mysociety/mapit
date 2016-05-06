# A control file for importing Boundary-Line.
# Not all areas have ONS codes, so we have to have something
# manual to e.g. tell us if some WMC have changed.
#
# Things without new ONS codes: CED
#
# This edition of Boundary-Line uses the new SNAC codes


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""
    return False


def patch_boundary_line(name, ons_code, type):
    """Used to fix mistakes in Boundary-Line. This patch function should return
    True if we want to ignore the provided ONS code (and match only on unit
    ID), or a new ONS code to replace it."""

    # Two incorrect IDs given in the source
    if name == 'Badgers Mount CP' and type == 'CPC' and ons_code == 'E04012604':
        return 'E04012605'
    if name == 'Shoreham CP' and type == 'CPC' and ons_code == 'E04012605':
        return 'E04012606'

    return False
