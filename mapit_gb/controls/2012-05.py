# A control file for importing May 2012 Boundary-Line. This control file
# assumes previous Boundary-Lines have been imported, because it uses that
# information. If this is a first import, use the first-gss control file.

from areas.models import Area, Generation


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match against ONS code,
       or an Area to be used as an override instead"""

    # There is a problem, in that users of this service, including ourselves,
    # have assumed a mapit ID is an identifier for a concept, rather than a
    # particular boundary. Until now, this has not really been an issue, but
    # this edition of Boundary-Line changes the boundary of four councils,
    # assigning them new ONS IDs in the process. This would cause some amount
    # of pain for code that assumes e.g. ID 2579 is the concept of Glasgow City
    # Council, rather than the boundary of Glasgow City Council from
    # generations 1 to 16 (but then not 17).
    #
    # Therefore, for the time being, we have decided to match up the new
    # boundaries with the current mapit IDs for these four councils. The old
    # boundaries will be lost from mapit, but could be loaded in manually from
    # the last edition of Boundary-Line if we really wanted, assigned new IDs.
    #
    # In the future, perhaps the current IDs should host the concept, for
    # continuity, and the current and historical boundaries are then available
    # under it in some way. Tricky.
    #
    # NB: After import_boundary_line is run with this control file, the GSS
    # codes of these four councils will need updating to their new entries, as
    # it will have maintained the old codes.

    if (type == 'UTA' and name in ('Glasgow City', 'East Dunbartonshire')) or (
            type == 'DIS' and name in ('St. Albans District (B)', 'Welwyn Hatfield District (B)')):
        current = Generation.objects.current()
        return Area.objects.get(
            names__name=name, names__type='O', generation_low__lte=current, generation_high__gte=current)

    # The following have had boundary changes for the 2012 elections, but all
    # have ONS codes and so can be ignored/ detected that way:
    #
    # Glasgow/E Dunb.	2010/353
    # Huntingdonshire	2010/684
    # Epping Forest	2011/2764 (minor)
    # Swansea		2011/2932
    # Swindon		2012/2
    # Hartlepool	2012/3
    # Rugby		2012/4
    # Broxbourne	2012/159
    # Daventry		2012/160
    # Rushmoor		2012/161
    # Welwyn/St Albans	2012/667

    return False
