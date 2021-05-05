# A control file for importing Boundary-Line.
# CEDs (county council electoral divisions) don't have ONS codes, so we would
# have to have something manual as this is a year of county council elections,
# but none of them has had structural boundary changes, hooray.


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""

    return False
