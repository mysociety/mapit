# This script is used after Boundary-Line has been imported to
# associate shapes with their parents. With the new coding
# system coming in, this could be done from a BIG lookup table; however,
# I reckon P-in-P tests might be quick enough...

from mapit.management.find_parents import FindParentsCommand


class Command(FindParentsCommand):
    parentmap = {
        # A District council ward's parent is a District council:
        'DIW': 'DIS',
        # A County council ward's parent is a County council:
        'CED': 'CTY',
        # A London borough ward's parent is a London borough:
        'LBW': 'LBO',
        # A London Assembly constituency's parent is the Greater London Authority:
        'LAC': 'GLA',
        # A Metropolitan district ward's parent is a Metropolitan district:
        'MTW': 'MTD',
        # A Unitary Authority ward (UTE)'s parent is a Unitary Authority:
        'UTE': 'UTA',
        # A Unitary Authority ward (UTW)'s parent is a Unitary Authority:
        'UTW': 'UTA',
        # A Scottish Parliament constituency's parent is a Scottish Parliament region:
        'SPC': 'SPE',
        # A Welsh Assembly constituency's parent is a Welsh Assembly region:
        'WAC': 'WAE',
        # A Civil Parish's parent is one of:
        #   District council
        #   Unitary Authority
        #   Metropolitan district
        #   London borough
        #   Scilly Isles
        'CPC': ('DIS', 'UTA', 'MTD', 'LBO', 'COI'),
        'CPW': 'CPC',
        # A Northern Ireland ward's parent is a Northern Ireland electoral area
        'LGW': 'LGE',
        # A Northern Ireland electoral area's parent is a Northern Ireland Council district
        'LGE': 'LGD',
    }
