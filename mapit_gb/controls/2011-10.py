# A control file for importing October 2011 Boundary-Line.
#
# Notes for this edition:
#
# * Two CEDs have had their names changed (no GSS codes so can't match up
# automatically) - Okhey Park ED to Oxhey Park ED, and Bested ED to Bersted ED.
# Here's the SQL used to fix this, using our own IDs (yours may differ):
#
# update areas_name set name='Oxhey Park ED' where area_id=15065 and type='O';
# update areas_area set name='Oxhey Park' where id=15065;
# update areas_name set name='Bersted ED' where area_id=53226 and type='O';
# update areas_area set name='Bersted' where id=53226;
#
# * Ordnance Survey changed the IDs of the wrong areas in two cases in the May
# 2011 Boundary-Line. E05004368 became E05008570, when it was E05004419 that
# should have become that. And E04008791 became E04012125 rather than
# E04008782. This edition corrects this, but the damage in mapit has already
# been done. Manually fixed before running import_boundary_line using the below
# SQL, again, using our hard-coded IDs.
#
# update areas_code set code='E05004368' where type='gss' and area_id=135066; -- Should have been all along
# delete from areas_code where code='E05004368' and type='gss' and area_id=4526;
# -- Can't have two areas with same GSS code
# update areas_code set code='E04008791' where type='gss' and area_id=135448;
# delete from areas_code where code='E04008791' and type='gss' and area_id=60017;
#
# This means the E04008782 and E05004419 areas contain new boundaries, rather
# than old, which were lost by the May 2011 import. This could be manually
# fixed if necessary by importing those two areas from the old Boundary-Line.


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match"""

    return False
