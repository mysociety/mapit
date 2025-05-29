# This script is to be run as a one-off to fix up some geometries in the May
# 2016 edition of Boundary-Line that are incorrect.

from django.core.management.base import BaseCommand
from mapit.models import Area, CodeType, Generation, Geometry


class Command(BaseCommand):
    help = 'Fix the UK Boundary-Line import for May 2016'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    code_version = CodeType.objects.get(code='gss')

    def get_area(self, code):
        area = Area.objects.get(codes__code=code, codes__type=self.code_version)
        assert area.polygons.count() == 1
        return area

    def get_generation_prior_to_current(self):
        latest_on = Generation.objects.filter(active=True).order_by('-id')
        if latest_on:
            return latest_on[1]
        return None

    def handle(self, **options):
        # The area that has been included as Cheriton and Bishops Sutton should
        # be part of Alresford & Itchen Valley.
        area_to_add_to = self.get_area('E05010995')  # Alresford & Itchen Valley
        area_to_remove = self.get_area('E05004654')  # Cheriton and Bishops Sutton

        self.stdout.write('Copying the area of %s to %s' % (area_to_remove, area_to_add_to))
        polygon = area_to_remove.polygons.all()[0]
        polygon_copy = Geometry(area=area_to_add_to, polygon=polygon.polygon)

        lower_generation = self.get_generation_prior_to_current()
        self.stdout.write('Setting the generation_high of %s to %s' % (area_to_remove, lower_generation))
        area_to_remove.generation_high = lower_generation
        if lower_generation is None:
            self.stdout.write('Only one generation, so setting generation_low to None too')
            area_to_remove.generation_low = None

        if options['commit']:
            polygon_copy.save()
            area_to_remove.save()
