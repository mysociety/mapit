# This script is used after Boundary-Line has been imported to
# associate shapes with their parents. With the new coding
# system coming in, this could be done from a BIG lookup table; however,
# I reckon P-in-P tests might be quick enough...

from optparse import make_option
from django.core.management.base import NoArgsCommand
from mapit.models import Area, Generation


class Command(NoArgsCommand):
    help = 'Find parents for shapes'
    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_noargs(self, **options):
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

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
        }
        for area in Area.objects.filter(
            type__code__in=parentmap.keys(),
            generation_low__lte=new_generation, generation_high__gte=new_generation,
        ):
            parent = None
            for polygon in area.polygons.all():
                try:
                    args = {
                        'polygons__polygon__contains': polygon.polygon.point_on_surface,
                        'generation_low__lte': new_generation,
                        'generation_high__gte': new_generation,
                    }
                    if isinstance(parentmap[area.type.code], str):
                        args['type__code'] = parentmap[area.type.code]
                    else:
                        args['type__code__in'] = parentmap[area.type.code]
                    parent = Area.objects.get(**args)
                    break
                except Area.DoesNotExist:
                    continue
            if not parent:
                raise Exception("Area %s does not have a parent?" % (self.pp_area(area)))
            if area.parent_area != parent:
                print("Parent for %s was %s, is now %s" % (
                    self.pp_area(area), self.pp_area(area.parent_area), self.pp_area(parent)))
                if options['commit']:
                    area.parent_area = parent
                    area.save()

    def pp_area(self, area):
        if not area:
            return "None"
        return "%s [%d] (%s)" % (area.name, area.id, area.type.code)
