# This script is used after Boundary-Line has been imported to
# associate shapes with their parents. With the new coding
# system coming in, this could be done from a BIG lookup table; however,
# I reckon P-in-P tests might be quick enough...

from django.core.management.base import NoArgsCommand
from mapit.areas.models import Area, Generation

class Command(NoArgsCommand):
    help = 'Find parents for shapes'

    def handle_noargs(self, **options):
        current_generation = Generation.objects.current()
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
            type__in=parentmap.keys(),
            generation_low__lte=new_generation, generation_high__gte=new_generation,
        ):
            polygon = area.polygons.all()[0]
            try:
                args = {
                    'polygons__polygon__contains': polygon.polygon.point_on_surface,
                    'generation_low__lte': new_generation,
                    'generation_high__gte': new_generation,
                }
                if isinstance(parentmap[area.type], str):
                    args['type'] = parentmap[area.type]
                else:
                    args['type__in'] = parentmap[area.type]
                parent = Area.objects.get(**args)
                print "Parent for %s [%d] (%s) is %s [%d] (%s)" % (area.name, area.id, area.type, parent.name, parent.id, parent.type)
            except Area.DoesNotExist:
                raise Exception, "Area %s [%d] (%s) does not have a parent?" % (area.name, area.id, area.type)
            if area.parent != parent:
                area.parent = parent
                area.save()

