# A control file for importing Boundary-Line.
# CEDs (county council electoral divisions) don't have ONS codes, so we have to
# have something manual as this is a year of county council boundary changes.
#
# OS release notes are at https://docs.os.uk/os-downloads/addressing-and-location/boundary-line/release-notes/may-2025
#
# The following English counties have had full boundary changes:
# Derbyshire - https://www.legislation.gov.uk/uksi/2024/1189/contents/made
# Gloucestershire - https://www.legislation.gov.uk/uksi/2025/34/contents/made
# Oxfordshire - https://www.legislation.gov.uk/uksi/2025/33/contents/made
# Staffordshire - https://www.legislation.gov.uk/uksi/2024/1184/contents/made
# Worcestershire - https://www.legislation.gov.uk/uksi/2024/1176/contents/made
#
# Unitaries with boundary changes are the following, but we spot them
# automatically by GSS code: Buckinghamshire, Durham, North Northamptonshire,
# Northumberland, Shropshire, West Northamptonshire

from mapit.models import Area, Generation, CodeType

COUNTIES_CHANGED = ["%s County Council" % c for c in [
    'Derbyshire', 'Gloucestershire', 'Oxfordshire', 'Staffordshire', 'Worcestershire'
]]
COUNTIES_NOT_CHANGED = ["%s County Council" % c for c in [
    'Cambridgeshire', 'Devon', 'Dorset', 'East Sussex', 'Essex', 'Hampshire',
    'Hertfordshire', 'Kent', 'Lancashire', 'Leicestershire', 'Lincolnshire',
    "Norfolk", "Northamptonshire", "North Yorkshire", 'Nottinghamshire',
    "Somerset", "Suffolk", "Surrey", 'Warwickshire', 'West Sussex'
]]


def code_version():
    return 'gss'


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS/unit_id code, or an Area to be used as an override instead."""

    current = Generation.objects.current()
    if not current:  # Fresh import
        return False

    # The boundary between Maidstone Rural West and Maidstone Central is
    # incorrect (the release notes say they did not get the fixed amendment in
    # in time). There was a change, but a much smaller one than what is
    # incorrectly included, so better to keep the old boundaries, as less wrong
    if type == 'CED' and name in ('Maidstone Rural West ED', 'Maidstone Central ED'):
        print(f"* Skipping {name} import")
        area = Area.objects.get(
            names__name=name, names__type__code='O', generation_low__lte=current, generation_high__gte=current)
        return area

    # Another repeat of 2012-05/2013-10/2018-05/2019-05 comments; still nothing
    # has changed, I'm doing the dance the same as last time.

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

    if type == 'MTD' and name in ('Barnsley District (B)', 'Sheffield District (B)'):
        print(f"* Updating {name}")
        # 1. Create a deep copy of the existing area with a new ID
        area = Area.objects.get(
            names__name=name, names__type__code='O', generation_low__lte=current, generation_high__gte=current)
        area_id = area.id
        area_polygons = list(area.polygons.all())
        area_codes = list(area.codes.all())
        area_names = list(area.names.all())
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

    # Some UTAs have had boundary changes, but have ONS codes and so can be
    # ignored/ detected that way.
    if type != 'CED':
        return False

    # Make sure CEDs are loaded *after* CTY
    area_within = Area.objects.filter(type__code='CTY', polygons__polygon__contains=geometry.geos.point_on_surface)[0]
    if area_within.name in COUNTIES_CHANGED:
        return True
    elif area_within.name in COUNTIES_NOT_CHANGED:
        return False
    raise Exception("Bad county name given: %s" % area_within.name)
