# A control file for importing May 2023 Boundary-Line.

def check(name, type, country, geometry, ons_code, **args):
    """Should return True if this area is NEW, False if we should match against
    an ONS code, or an Area to be used as an override instead."""

    # Suffolk boundaries from 2025 have been put in this Boundary-Line.  Skip
    # all CEDs, and hope there have been no other changes (none according to
    # the release notes, anyway, which makes sense because boundary changes
    # come into effect when there's a county council election and there aren't
    # any this year).
    if type == 'CED':
        return 'SKIP'

    # Bentham Ward was part of Craven District Council; both were abolished in
    # April 2023. Yet it has somehow slipped through into Boundary-Line. Our
    # import script errored on this immediately.
    if type == 'DIW' and name == 'Bentham Ward':
        return 'SKIP'

    # This is the default
    return False
