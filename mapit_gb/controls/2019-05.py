# A control file for importing Boundary-Line.

from mapit.models import Area, Generation, CodeType


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS/unit_id code, or an Area to be used as an override instead."""

    current = Generation.objects.current()
    if not current:  # Fresh import
        return False

    # These areas had name corrections in May 2019 Boundary-Line,
    # so find the misnamed entries if present
    if type == 'CED' and name == "Bishop's Stortford West ED":
        return Area.objects.get(
            names__type__code='O', names__name='Bishops Stortford West ED',
            codes__type__code='unit_id', codes__code=41708,
            generation_low__lte=current, generation_high__gte=current)
    elif type == 'CED' and name == "Bishop's Stortford East ED":
        return Area.objects.get(
            names__type__code='O', names__name='Bishops Stortford East ED',
            codes__type__code='unit_id', codes__code=41709,
            generation_low__lte=current, generation_high__gte=current)
    elif type == 'CED' and name == "Bishop's Stortford Rural ED":
        return Area.objects.get(
            names__type__code='O', names__name='Bishops Stortford Rural ED',
            codes__type__code='unit_id', codes__code=41707,
            generation_low__lte=current, generation_high__gte=current)

    # Another repeat of 2012-05/2013-10/2018-05 comments; stil nothing has
    # changed, I'm doing the dance the same as last time.

    # There is a problem, in that users of this service, including ourselves,
    # have assumed a mapit ID is an identifier for a concept, rather than a
    # particular boundary. Until now, this has not really been an issue, but
    # this edition of Boundary-Line changes the boundary of two councils,
    # assigning them new ONS IDs in the process. This would cause some amount
    # of pain for code that assumes e.g. ID 2579 is the concept of Glasgow City
    # Council, rather than the boundary of Glasgow City Council from
    # generations 1 to 16 (but then not 17).
    #
    # Therefore, for the time being, we have decided to match up the new
    # boundaries with the current mapit IDs for these four councils.
    #
    # In the future, perhaps the current IDs should host the concept, for
    # continuity, and the current and historical boundaries are then available
    # under it in some way. Tricky.

    if type == 'UTA' and name in ('Glasgow City', 'North Lanarkshire'):
        # 1. Create a deep copy of the existing area with a new ID
        area = Area.objects.get(
            names__name=name, names__type__code='O', generation_low__lte=current, generation_high__gte=current)
        area_id = area.id
        area_polygons = area.polygons.all()
        area_codes = area.codes.all()
        area_names = area.names.all()
        area.pk = None
        if commit:
            area.save()
            for data in [area_polygons, area_codes, area_names]:
                for thing in data:
                    thing.pk = None
                    thing.area = area
                    thing.save()

        # 2. Update the existing area with the new boundary/generation IDs
        area = Area.objects.get(id=area_id)
        new_generation = Generation.objects.new()
        area.generation_low = new_generation
        if commit:
            area.save()
            # Delete the old ONS code because that only applies to the old boundary
            area.codes.filter(type=CodeType.objects.get(code='ons')).delete()
            # Update the GSS code because it's what the main script will then use, oddly.
            area.codes.update_or_create(type=CodeType.objects.get(code='gss'), defaults={'code': ons_code})

        return area

    # Everything else can be ignored/ detected via changes in GSS codes
    return False
