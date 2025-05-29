# A control file for importing October 2013 Boundary-Line.

# This control file assumes previous Boundary-Lines have been imported,
# because it uses that information. If this is a first import, use the
# first-gss control file.

from ..models import Area, Generation


def code_version():
    return 'gss'


def check(name, type, country, geometry, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    # See 2012-05.py for a better explanation of what we're doing here and why.

    # We're basically manually overriding the area that gets updated for some
    # of the areas in this edition of the boundary line, because we want their
    # Mapit ID numbers to stay the same, but they have new GSS codes, so they
    # would normally be created as new areas.

    # The following Welsh Assembly regions and constituencies changed as part
    # of SI 2011/2987, but we don't need to worry about them because we don't
    # store their IDs anywhere that'll break.
    # 'South Wales West Assembly ER',
    # 'South Wales East Assembly ER',
    # 'South Wales Central Assembly ER',
    # 'Mid and West Wales Assembly ER'
    # These Welsh constituencies also changed, but we don't need to worry
    # about them either:
    # 'Brecon and Radnorshire Assembly Const',
    # 'Vale of Glamorgan Assembly Const',
    # 'Pontypridd Assembly Const',
    # 'Cardiff North Assembly Const',
    # 'Merthyr Tydfil and Rhymney Assembly Const',
    # 'Ogmore Assembly Const',
    # 'Cardiff South and Penarth Assembly Const',

    # These districts changed as part of SI 2013/596, we need to keep their
    # IDs the same because FixMyStreet stores them in it's DB.
    overriden_dis_areas = (
        'East Hertfordshire District',
        'Stevenage District (B)'
    )
    # These wards which changed because of 2013/596, but we don't mind that:
    # Walkern Ward - DIW
    # Manor Ward - DIW

    # These Unitary Authorities which changed in 2013/595, we also need to
    # maintain old IDs for:
    # Northumberland
    # Gateshead District (B)

    # There were two ward which changed in 2013/595 too, but we don't care
    # about that.
    # South Tynedale ED - UTE
    # Chopwell & Rowlands Gill - MTW

    # The following Parish Council's changed, but because we don't rely on
    # their ID numbers, we don't care that they make new ones.
    # Walkern CP - CPC
    # Wootton CP - CPC
    # Hardingstone CP - CPC
    # Upton CP - CPC
    # Great Houghton CP - CPC
    # Hedley CP - CPC
    # Collingtree CP - CPC

    # These are new and they actually are new, but they have a GSS code, so
    # the import command will find them on it's own:
    # West Hunsbury CP - CPC
    # Hunsbury Meadows CP - CPC

    current = Generation.objects.current()

    if (type == 'UTA' and name == 'Northumberland') \
       or (type == 'MTD' and name == 'Gateshead District (B)') \
       or (type == 'DIS' and name in overriden_dis_areas):
        return Area.objects.get(
            names__name=name, names__type__code='O',
            generation_low__lte=current, generation_high__gte=current)

    # This is the default
    return False
