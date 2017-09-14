import csv
import re
import sys

from django.core.management.base import BaseCommand
from mapit.models import Area, Generation, CodeType


class Command(BaseCommand):
    help = 'Adds GSS codes to new wards available in 2016 OS forward dated polygons'

    def handle(self, **options):
        code_type = CodeType.objects.get(code='gss')
        generation = Generation.objects.current()

        c = csv.reader(open('wd16.csv'))
        next(c)

        for row in c:
            gss = row[0]
            name = row[1]
            si_title = row[3]
            place = re.match('The (.*?) \(', si_title).group(1)

            print '*', name, gss, place,

            areas = list(Area.objects.filter(type__code='16W', name=name))
            if len(areas) == 0:
                areas = list(Area.objects.filter(type__code='16W', name=name.replace(' and ', ' & ')))

            if len(areas) == 1:
                area = areas[0]
            elif len(areas) == 0:
                print "ARGH"
                sys.exit(1)
            else:
                for a in areas:
                    councils = list(Area.objects.intersect('intersects', a, ['DIS', 'UTA'], generation))
                    for c in councils:
                        if place in c.name:
                            area = a
                            break
            print ' ', area
            area.codes.update_or_create(type=code_type, defaults={'code': gss})
