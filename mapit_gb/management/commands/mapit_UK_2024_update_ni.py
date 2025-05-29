# This script is to be run as a one-off after an import of the June 2024 OS
# Boundary-Line in order to update the Northern Ireland UK constituencies.
# It assumes you previously already loaded in all the new boundaries in the
# 'WMCF' area type, taken from
# https://pages.mysociety.org/2025-constituencies/datasets/parliament_con_2025/latest

from django.core.management.base import BaseCommand
from mapit.models import Area, Type


def copy_object(obj, new_area):
    obj.pk = None
    obj.area = new_area
    obj.save()
    print(' ', obj)


class Command(BaseCommand):
    help = 'Update the NI constituencies after the 2024 election'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        areas = Area.objects.filter(type__code='WMCF', country__code='N')
        wmc_type = Type.objects.get(code='WMC')
        for area in areas:
            polygons = list(area.polygons.all())
            names = list(area.names.all())
            codes = list(area.codes.all())
            area.pk = None
            area.type = wmc_type
            area.generation_low_id = 55
            area.generation_high_id = 55
            area.save()
            print(area)
            for polygon in polygons:
                copy_object(polygon, area)
            for name in names:
                copy_object(name, area)
            for code in codes:
                copy_object(code, area)
