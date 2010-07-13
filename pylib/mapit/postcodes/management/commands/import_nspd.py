# This script is used to import Northern Ireland postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/
# 
# The fields of NSPD Open CSV file are:
#   Postcode (7), Postcode (8), Postcode (sp), Start date, End date, County,
#   council, ward, usertype, Easting, Northing, quality SHA, IT cluster,
#   country, GOR, Stats region, Parliamentary constituency, Euro region,
#   TEC/LEC, Travel to Work area, Primary Care Org, NUTS, 1991 census ED,
#   1991 census ED, ED indicator, Pre-July 2006 SHA, LEA, Pre 2002 Health
#   Authority, 1991 ward code, 1991 ward code, 1998 ward code, 2005 stats ward,
#   OA code, OA indicator, CAS ward, National Park, SOA (Lower), Datazone, SOA
#   (Middle), Urban/rural, Urban/rural, Urban/rural, Intermediate, SOA (NI), OA
#   classification, Pre October 2006 PCO

# TODO
# Read in ni-electoral-areas file that maps district+ward name to electoral area name/Area
# Read in SNAC files (one pre WMC change, one post) that map ward to district to constituency

import sys
import csv
from django.contrib.gis.geos import Point
from django.core.management.base import BaseCommand
from mapit.postcodes.models import Postcode
from mapit.areas.models import Area, Generation

class Command(BaseCommand):
    def handle(self, *args, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        euro_area, created = Area.objects.get_or_create(country='N', type='EUR',
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            defaults = { 'generation_low': new_generation, 'generation_high': new_generation }
        )
        euro_area.names.create(type='S', name='Northern Ireland')

        count = 0
        for row in csv.reader(sys.stdin):
            if row[4]: continue # Terminated postcode
            postcode = row[0].strip().replace(' ', '')
            if postcode[0:2] != 'BT': continue # Only importing NI from NSPD

            ons_code = '%s%s%s' % tuple(row[5:8])
            print postcode, ons_code, row[9:12]
            continue

            # Create/update the postcode
            location = Point(map(float, row[9:11]), srid=27700)
            try:
                pc = Postcode.objects.get(postcode=postcode)
                pc.location = location
                pc.save()
            except Postcode.DoesNotExist:
                pc = Postcode.objects.create(postcode=postcode, location=location)

            # Create/update the areas
            parliament = row[16]
            try:
                ward = Area.objects.get(codes__type='ons', codes__code=ons_code)
                electoral_area = ward.parent_area
                council = electoral_area.parent_area
            except Area.DoesNotExist:
                ward = Area.objects.create(country='N', type='LGW')
                ward.codes.create(type='ons', code=ons_code)
                # Fetch ward name from ONS code
                ward.names.create(type='S', name='')
                # Fetch EA name from ward code or name
                electoral_area, created = Area.objects.get_or_create(country='N', type='LGE', names__type='S', names__name='')
                ward.parent_area = electoral_area
                # Fetch council name and code from ward code or name
                council, created = Area.objects.get_or_create(country='N', type='LGD', codes__type='ons', codes__code='', names__type='S', names__name='')
                electoral_area.parent_area = council

            # Fetch Assembly constituency name from OLD SNAC
            assembly, created = Area.objects.get_or_create(country='N', type='NIE', names__type='S', name='')
            # Fetch Parliamentary constituency code and name from NEW SNAC
            parliament, created = Area.objects.get_or_create(country='N', type='WMC', codes__type='ons', codes__code='', names__type='S', name='')

            # Associate all these geometry-less areas with this postcode
            pc.areas.add(ward, electoral_area, council, assembly, parliament, euro_area)

            count += 1
            if count % 10000 == 0:
                print "Imported %d" % count
            
