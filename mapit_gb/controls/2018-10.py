# A control file for importing Boundary-Line.

from mapit.models import Area, Generation


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS/unit_id code, or an Area to be used as an override instead."""

    current = Generation.objects.current()

    # These areas had name corrections inOctober 2018 Boundary-Line,
    # so find the misnamed entries if present
    if type == 'CED' and name == 'Uckfield South With Framfield ED':
        return Area.objects.get(
            names__type__code='O', names__name='Uckfield South With Framfield',
            codes__type__code='unit_id', codes__code=44756,
            generation_low__lte=current, generation_high__gte=current)
    elif type == 'CED' and name == 'Mendip Hills ED':
        return Area.objects.get(
            names__type__code='O', names__name='Mendip Hiils ED',
            codes__type__code='unit_id', codes__code=41675,
            generation_low__lte=current, generation_high__gte=current)

    return False
