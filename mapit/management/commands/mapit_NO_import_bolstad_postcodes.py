# This script is used to import Norwegian postcode information from
# http://www.erikbolstad.no/geo/noreg/postnummer/, released by the
# Erik Bolstad.
# http://www.erikbolstad.no/nedlasting/postnummer-utf8.txt
# 
# The fields of the CSV file are:
#  Postnummer, Poststad, Bruksomraade, Kommunenummer, Kommune, Fylke,
#  Lat, Lon, Merknad

import csv
from django.contrib.gis.geos import Point
from mapit.management.command_utils import PostcodeCommand

class Command(PostcodeCommand):
    help = 'Import Norwegian postcodes from the Erik Bolstad data set'
    args = '<CSV files>'
    often = 1000

    def handle_label(self, file, **options):
        csv.register_dialect('tabs', delimiter='\t')
        for row in csv.reader(open(file), dialect='tabs'):
            if row[6] == 'Lat': continue # skip header
            postcode = row[0].strip().replace(' ', '')
#            print "'%s' '%s' '%s'" % (row, row[6:7], row[7:8])
            lat = float(row[6])
            lon = float(row[7])
            location = Point(lon, lat, srid=4326)
            self.do_postcode(postcode, location)
        self.print_stats()

