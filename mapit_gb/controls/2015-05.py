# A control file for importing May 2015 Boundary-Line.

# This control file assumes previous Boundary-Lines have been imported,
# because it uses that information. If this is a first import, use the
# first-gss control file.


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    # There are lots of new things in this edition of boundary line, but none
    # of them are things which we have to manually override, which is nice.

    # New areas, by type:

    # County electoral divisions
    # New area: CED None 44530 Wyreside ED
    # Geometry of None CED Earls Barton not valid
    # Geometry of None CED Hatton Park not valid

    # Metropolitan wards
    # Doncaster (SI 2015/114)

    # Wards, in range E05009491-E05010773
    # Upwards of 50 councils with boundary changes
    # Geometry of E05010034 DIW Harrowden & Sywell Ward not valid
    # Geometry of E05010039 DIW Redwell Ward not valid

    # London Borough Wards
    # Geometry of E05009392 LBW Colville not valid
    # Geometry of E05009400 LBW Pembridge not valid

    # Unitary Authority wards
    # Darlington (2014/3338)
    # Herefordshire (2014/20)
    # Leicester (2014/3339)
    # Middlesbrough (2014/1188)
    # North Somerset (2014/3291)
    # Poole (2015/73)
    # Swindon (2015/116)
    # Telford & Wrekin (2014/1910)
    # York (2014/3289)

    # Parish Councils, most IDs from E04012345-E04012470
    # Geometry of E04006883 CPC Great Harrowden not valid

    # This is the default
    return False
