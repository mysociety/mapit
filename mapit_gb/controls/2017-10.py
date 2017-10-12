# A control file for importing Boundary-Line.

from mapit.models import Area, Generation


def check(name, type, country, geometry, ons_code, commit, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS/unit_id code, or an Area to be used as an override instead."""

    current = Generation.objects.current()

    # May 2017 Boundary-Line gave Clydebank Central the wrong ID,
    # update/return the relevant row if present
    if type == 'UTW' and ons_code == 'S13003126':
        a = Area.objects.get(codes__type__code='gss', codes__code='S13003136')
        if commit:
            a.codes.update_or_create(type__code='gss', defaults={'code': 'S13003126'})
        return a

    # May 2017 Boundary-Line incorrectly assigned Flintshire's Halkyn ED's new
    # GSS ID to Brynford ED, meaning you may now have two identical Brynfords,
    # and you lost the old Halkyn boundary. Let us try and resolve the mess.
    if type == 'UTE' and ons_code == 'W05001005':
        # First, we want Halkyn to be entered as a new area. The old Halkyn
        # won't have its correct boundary and will be one generation out.
        return True
    if type == 'UTE' and ons_code == 'W05000186':
        # First, get rid of any existing W05000186 code.
        # Then rename any existing W05001005 Brynford to W05000186.
        # Then any existing Brynford will match to that Brynford.
        try:
            a = Area.objects.get(codes__type__code='gss', codes__code='W05000186')
            if commit:
                a.codes.filter(type__code='gss').delete()
        except Area.DoesNotExist:
            pass
        try:
            # Include name here so we don't match against the new correct Halkyn
            a = Area.objects.get(codes__type__code='gss', codes__code='W05001005', name='Brynford')
            if commit:
                a.codes.update_or_create(type__code='gss', defaults={'code': 'W05000186'})
            return a
        except Area.DoesNotExist:
            pass

    # These areas were incorrectly named in May 2017 Boundary-Line,
    # so find the misnamed entries if present
    if type == 'CED' and name == 'Uckfield North ED':
        return Area.objects.get(
            names__type__code='O', names__name='Uckfield ED',
            codes__type__code='unit_id', codes__code=2741,
            generation_low__lte=current, generation_high__gte=current)
    elif type == 'CED' and name == "St. Leonard's Forest ED":
        return Area.objects.get(
            names__type__code='O', names__name="St. Leonard's Forset ED",
            codes__type__code='unit_id', codes__code=44768,
            generation_low__lte=current, generation_high__gte=current)

    return False
