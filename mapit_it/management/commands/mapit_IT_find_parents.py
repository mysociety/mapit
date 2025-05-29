# This script is used after ISTAT administrative areas have been imported,
# to associate shapes with their parents.

from mapit.management.find_parents import FindParentsCommand


class Command(FindParentsCommand):
    parentmap = {
        # A Comune's parent is a Province:
        'COM': 'PRO',
        # A Province's parent is a Regione:
        'PRO': 'REG',
    }
