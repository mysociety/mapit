# A control file for importing May 2024 Boundary-Line.

from mapit.models import Area, Generation


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    if type != 'CED':
        return False

    current = Generation.objects.current()
    if not current:  # Fresh import
        return False

    # All the unit IDs have changed in this release. CEDs don't have ONS codes
    # to match on, so instead we have to match on name (they should all be the same)
    area = Area.objects.get(
        type__code='CED',
        names__type__code='O', names__name=name,
        generation_low__lte=current, generation_high__gte=current,
        polygons__polygon__contains=geometry.geos.point_on_surface
    )
    return area
