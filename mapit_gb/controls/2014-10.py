# A control file for importing October 2014 Boundary-Line.

# This control file assumes previous Boundary-Lines have been imported,
# because it uses that information. If this is a first import, use the
# first-gss control file.


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    return False
