# This script is used to import Norwegian postcode information from
# http://www.erikbolstad.no/geo/noreg/postnummer/, released by the
# Erik Bolstad.
# http://www.erikbolstad.no/nedlasting/postnummer-utf8.txt
# 
# The fields of Code-Point Open CSV file are:
#  Postnummer, Poststad, Bruksomraade, Kommunenummer, Kommune, Fylke,
#  Lat, Lon, Merknad

import csv
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
from mapit.postcodes.models import Postcode

class Command(LabelCommand):
    help = 'Import Norwegian postcodes from the Erik Bolstad data set'
    args = '<CSV files>'
    count = { 'total': 0, 'updated': 0, 'unchanged': 0, 'created': 0 }

    def print_stats(self):
        print "Imported %d (%d new, %d changed, %d same)" % (
            self.count['total'], self.count['created'],
            self.count['updated'], self.count['unchanged']
        )

    def handle_label(self, file, **options):
        csv.register_dialect('tabs', delimiter='\t')
        for row in csv.reader(open(file), dialect='tabs'):
            postcode = row[0].strip().replace(' ', '')
#            print "'%s' '%s' '%s'" % (row, row[6:7], row[7:8])
            if row[6] == 'Lat': continue # skip header
            lat = float(row[6])
            lon = float(row[7])
            location = Point(lon, lat, srid=4326)
            # Want to compare co-ordinates so can't use straightforward
            # update_or_create
            try:
                pc = Postcode.objects.get(postcode=postcode)
                if pc.location[0] != location[0] or \
                        pc.location[1] != location[1]:
                    pc.location = location
                    pc.save()
                    self.count['updated'] += 1
                else:
                    self.count['unchanged'] += 1
            except Postcode.DoesNotExist:
                Postcode.objects.create(postcode=postcode, location=location)
                self.count['created'] += 1
            self.count['total'] += 1
            if self.count['total'] % 1000 == 0:
                self.print_stats()
        self.print_stats()

