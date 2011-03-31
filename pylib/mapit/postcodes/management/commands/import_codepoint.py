# This script is used to import Great Britain postcode information from
# Code-Point Open, released by the Ordnance Survey. Compared to the
# scripts we had in 2003, and that the data is free, I'm in heaven.
# 
# The fields of Code-Point Open CSV file are:
#   Postcode, Quality, 8 blanked out fields, Easting Northing, Country,
#   NHS region, NHS health authority, County, District, Ward, blanked field
#
# XXX The February 2011 release has announced that the blanked out fields wil
# be removed at some point. This code (specifically line 24) will have to be
# modified then, plus some way of dealing with old Code-Points.

import csv
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
from mapit.postcodes.models import Postcode

class Command(LabelCommand):
    help = 'Import OS Code-Point Open postcodes'
    args = '<Code-Point CSV files>'
    count = { 'total': 0, 'updated': 0, 'unchanged': 0, 'created': 0 }
    def handle_label(self, file, **options):
        for row in csv.reader(open(file)):
            if row[1] == '90': continue # Bad postcode
            postcode = row[0].strip().replace(' ', '')
            location = Point(map(float, row[10:12]), srid=27700)
            # Want to compare co-ordinates so can't use straightforward update_or_create
            try:
                pc = Postcode.objects.get(postcode=postcode)
                pc.location.transform(27700) # Postcode locations are stored as WGS84
                if round(pc.location[0]) != location[0] or round(pc.location[1]) != location[1]:
                    pc.location = location
                    pc.save()
                    self.count['updated'] += 1
                else:
                    self.count['unchanged'] += 1
            except Postcode.DoesNotExist:
                Postcode.objects.create(postcode=postcode, location=location)
                self.count['created'] += 1
            self.count['total'] += 1
            if self.count['total'] % 10000 == 0:
                print "Imported %d (%d new, %d changed, %d same)" % (
                    self.count['total'], self.count['created'], self.count['updated'], self.count['unchanged']
                )

