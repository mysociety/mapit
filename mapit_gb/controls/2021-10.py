# A control file for importing October 2021 Boundary-Line.


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    return False
