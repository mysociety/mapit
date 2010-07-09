import sys
import csv
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from postcodes.models import Postcode

class Command(BaseCommand):
    def handle(self, *args, **options):
        count = 0
        for row in csv.reader(sys.stdin):
            args = {
                'postcode': row[0].strip().replace(' ', ''),
                'location': Point(map(float, row[10:12])),
            }
            if not Postcode.objects.filter(postcode=args['postcode']).update(location=args['location']):
                Postcode.objects.create(**args)

            count += 1
            if count % 10000 == 0:
                print "Imported %d" % count

