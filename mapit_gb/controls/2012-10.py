# A control file for importing October 2012 Boundary-Line.
#
# Nothing special to do, hooray.


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""
    return False
