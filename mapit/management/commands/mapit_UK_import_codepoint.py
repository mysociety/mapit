# This script is used to import Great Britain postcode information from
# Code-Point Open, released by the Ordnance Survey. Compared to the
# scripts we had in 2003, and that the data is free, I'm in heaven.
# 
# The fields of a Code-Point Open CSV file before August 2011 are:
#   Postcode, Quality, 8 blanked out fields, Easting, Northing, Country,
#   NHS region, NHS health authority, County, District, Ward, blanked field
#
# The fields after August 2011, with blank fields removed and with new GSS
# codes, are: Postcode, Quality, Easting, Northing, Country, NHS region, NHS
# health authority, County, District, Ward

import csv
from django.contrib.gis.geos import Point
from mapit.management.command_utils import PostcodeCommand

class Command(PostcodeCommand):
    help = 'Import OS Code-Point Open postcodes'
    args = '<Code-Point CSV files>'
    often = 10000

    def handle_label(self, file, **options):
        for row in csv.reader(open(file)):
            if row[1] == '90': continue # Bad postcode
            postcode = row[0].strip().replace(' ', '')
            easting_column = 2 if len(row) == 10 else 10 # A new Code-Point only has 10 columns
            location = Point(map(float, row[easting_column:easting_column+2]), srid=27700)
            self.do_postcode(postcode, location)
        self.print_stats()
