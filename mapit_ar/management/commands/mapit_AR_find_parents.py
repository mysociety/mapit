# You should use this after mapit_AR_import_boundaries to make sure
# that each department has the correct province set as its parent.

from mapit.management.find_parents import FindParentsCommand


class Command(FindParentsCommand):
    parentmap = {
        # A Department's parent is a Province:
        'DPT': 'PRV',
    }
