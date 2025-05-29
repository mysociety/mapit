# This script is to be run as a one-off after the 2024 UK General Election
# to update the Northern Ireland Assembly boundaries to match the UK
# constituencies, as per section 33 of the Northern Ireland Act 1998.

from django.core.management.base import BaseCommand
from mapit.models import Area, Generation, Type


def save(obj, options, space=''):
    obj.pk = None
    if options['commit']:
        obj.save()
    print(space, obj)


class Command(BaseCommand):
    help = 'Update the NI Assembly constituencies after the 2024 election'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        areas = Area.objects.filter(type__code='WMC', country__code='N', generation_high=Generation.objects.current())
        nie_type = Type.objects.get(code='NIE')
        generation = Generation.objects.new()
        for area in areas:
            polygons = list(area.polygons.all())
            names = list(area.names.all())
            area.type = nie_type
            area.generation_low = generation
            area.generation_high = generation
            save(area, options)
            for data in [polygons, names]:
                for obj in data:
                    obj.area = area
                    save(obj, options, '  ')
