# This management command can be used by subclassing to associate areas with
# their "parents". Provide a "parentmap" in your subclass mapping child area
# type to parent area type.

from django.core.management.base import BaseCommand
from mapit.models import Area, Generation


class FindParentsCommand(BaseCommand):
    help = 'Find parents for shapes'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    @property
    def parentmap(self):
        raise NotImplementedError("You must specify a parentmap attribute in your subclass")

    def handle(self, **options):
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        for area in Area.objects.filter(
            type__code__in=self.parentmap.keys(),
            generation_low__lte=new_generation, generation_high__gte=new_generation,
        ):
            parent = None
            if int(options['verbosity']) >= 2:
                self.stdout.write("Processing %s" % (
                    self.pp_area(area)
                ))
            for polygon in area.polygons.all():
                try:
                    args = {
                        'polygons__polygon__contains': polygon.polygon.point_on_surface,
                        'generation_low__lte': new_generation,
                        'generation_high__gte': new_generation,
                    }
                    if isinstance(self.parentmap[area.type.code], str):
                        args['type__code'] = self.parentmap[area.type.code]
                    else:
                        args['type__code__in'] = self.parentmap[area.type.code]
                    parent = Area.objects.get(**args)
                    break
                except Area.DoesNotExist:
                    continue
            if not parent:
                raise Exception("Area %s does not have a parent?" % (self.pp_area(area)))
            if area.parent_area != parent:
                self.stdout.write("Parent for %s was %s, is now %s" % (
                    self.pp_area(area), self.pp_area(area.parent_area), self.pp_area(parent)))
                if options['commit']:
                    area.parent_area = parent
                    area.save()

    def pp_area(self, area):
        if not area:
            return "None"
        return "%s [%d] (%s)" % (area.name, area.id, area.type.code)
