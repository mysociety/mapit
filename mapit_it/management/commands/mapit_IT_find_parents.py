# This script is used after ISTAT administrative areas have been imported,
# to associate shapes with their parents.


from optparse import make_option
from django.core.management.base import NoArgsCommand
from mapit.models import Area, Generation

__author__ = 'guglielmo'

class Command(NoArgsCommand):
    help = 'Find parents for shapes'
    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_noargs(self, **options):
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        parentmap = {
            # A Comune's parent is a Province:
            'COM': 'PRO',
            # A Province's parent is a Regione:
            'PRO': 'REG',
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
                raise Exception, "Area %s does not have a parent?" % (self.pp_area(area))
            if area.parent_area != parent:
                print "Parent for %s was %s, is now %s" % (self.pp_area(area), self.pp_area(area.parent_area), self.pp_area(parent))
                if options['commit']:
                    area.parent_area = parent
                    area.save()

    def pp_area(self, area):
        if not area: return "None"
        return "%s [%d] (%s)" % (area.name, area.id, area.type.code)
