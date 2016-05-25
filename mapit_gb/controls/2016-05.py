# A control file for importing May 2016 Boundary-Line. This control file should
# be okay to run as a first import file also, it uses previous Boundary-Line
# information if present to fix up issues with the source data.

from mapit.models import Area, Generation


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against ONS code,
       or an Area to be used as an override instead"""

    if type in ('WAC', 'WAE'):
        # We might be in the situation where we have bad data, as OS provided
        # incorrect boundaries from October 2013 to May 2015 inclusive:
        # https://web.archive.org/web/20150922064012/https://www.ordnancesurvey.co.uk/business-and-government/help-and-support/products/boundary-line.html
        # The October 2015 MapIt import put the old boundaries in again as new
        # creations. Let's move the old boundaries to be new, as that's what
        # they are now, and push back the current boundary generation to cover
        # where they were.
        try:
            name = name.replace(' Assembly Const', '').replace(' Assembly ER', '')
            current = Area.objects.get(type__code=type, name=name, generation_high=Generation.objects.current())
            old_but_new = Area.objects.get(
                codes__type__code='gss', codes__code=ons_code, generation_high__lt=Generation.objects.current())
            assert current.generation_low.id == old_but_new.generation_high.id + 1
            print "* Wales change, before: %d %s (%d-%d), %d %s (%d-%d)" % (
                old_but_new.id, old_but_new.name, old_but_new.generation_low_id, old_but_new.generation_high_id,
                current.id, current.name, current.generation_low_id, current.generation_high_id)
            current.generation_low = old_but_new.generation_low
            if commit:
                current.save()
            old_but_new.generation_low = Generation.objects.new()
            old_but_new.generation_high = Generation.objects.new()
            print "  After: %d %s (%d-%d), %d %s (%d-%d)" % (
                current.id, current.name, current.generation_low_id, current.generation_high_id,
                old_but_new.id, old_but_new.name, old_but_new.generation_low_id, old_but_new.generation_high_id)
            return old_but_new
        except Area.DoesNotExist:
            pass

    if type == 'CPC' and name == 'Church Fenton CP':
        # Parish council removed in May 2015, now back.
        try:
            m = Area.objects.get(codes__type__code='gss', codes__code=ons_code)
            m.generation_high = Generation.objects.current()
            return m
        except Area.DoesNotExist:
            pass

    # The following have had full boundary changes for the 2016 elections, but
    # all have ONS codes and so can be ignored/ detected that way:
    #
    # Bristol           2015/1871
    # Cherwell          2015/1872
    # Colchester        2015/1859
    # Elmbridge         2016/301
    # Exeter            2016/65
    # Gloucester        2015/2026
    # Knowsley          2015/2036
    # Lincoln           2015/1461
    # Peterborough      2015/1858
    # Rochford          2015/1860
    # Sheffield         2015/1861
    # Stroud            2015/2034
    # Warrington        2016/115
    # Watford           2016/112
    # Welwyn Hatfield   2016/116
    # Winchester        2015/2063
    # Woking            2015/1462

    # The following have had related alterations due to parish changes, which
    # again can be ignored/detected by ONS code:
    #
    # Craven            2012/3150
    # West Oxfordshire  2012/2993

    return False
