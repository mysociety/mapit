# This script is used after Boundary-Line has been imported to
# associate shapes with their parents. With the new coding
# system coming in, this could be done from a BIG lookup table; however,
# I reckon P-in-P tests might be quick enough...

from django.core.management.base import NoArgsCommand
from mapit.models import Area, Generation

class Command(NoArgsCommand):
    help = 'Find parents for shapes'

    def handle_noargs(self, **options):
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        parentmap = {
            'DIW': 'DIS',
            'CED': 'CTY',
            'LBW': 'LBO',
            'LAC': 'GLA',
            'MTW': 'MTD',
            'UTE': 'UTA',
            'UTW': 'UTA',
            'SPC': 'SPE',
            'WAC': 'WAE',
            'CPC': ('DIS', 'UTA', 'MTD', 'LBO', 'COI'),
        }
        for area in Area.objects.filter(
            type__code__in=parentmap.keys(),
            generation_low__lte=new_generation, generation_high__gte=new_generation,
        ):
            polygon = area.polygons.all()[0]
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
            except Area.DoesNotExist:
                raise Exception, "Area %s does not have a parent?" % (self.pp_area(area))
            if area.parent_area != parent:
                print "Parent for %s was %s, is now %s" % (self.pp_area(area), self.pp_area(area.parent_area), self.pp_area(parent))
                area.parent_area = parent
                area.save()

    def pp_area(self, area):
        if not area: return "None"
        return "%s [%d] (%s)" % (area.name, area.id, area.type.code)
