# This script is used to import Northern Ireland postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/
# 
# The fields of NSPD Open CSV file are:
#   Postcode (7), Postcode (8), Postcode (sp), Start date, End date, County,
#   council, ward, usertype, Easting, Northing, quality, SHA, IT cluster,
#   country, GOR, Stats region, Parliamentary constituency, Euro region,
#   TEC/LEC, Travel to Work area, Primary Care Org, NUTS, 1991 census ED,
#   1991 census ED, ED indicator, Pre-July 2006 SHA, LEA, Pre 2002 Health
#   Authority, 1991 ward code, 1991 ward code, 1998 ward code, 2005 stats ward,
#   OA code, OA indicator, CAS ward, National Park, SOA (Lower), Datazone, SOA
#   (Middle), Urban/rural, Urban/rural, Urban/rural, Intermediate, SOA (NI), OA
#   classification, Pre October 2006 PCO

import csv
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
from django.db import transaction
from mapit.postcodes.models import Postcode
from mapit.areas.models import Area, Generation

class Command(LabelCommand):
    help = 'Imports Northern Ireland postcodes from the NSPD, using existing areas only'
    args = '<NSPD CSV file>'

    @transaction.commit_manually
    def handle_label(self, file, **options):
        euro_area = Area.objects.get(country__code='N', type__code='EUR')

        # Read in new ONS code to names, look up existing wards and Parliamentary constituencies
        snac = csv.reader(open('../../data/snac-2009-ni-cons2ward.csv'))
        snac.next()
        code_to_area = {}
        for parl_code, parl_name, ward_code, ward_name, district_code, district_name in snac:
            ward_code = ward_code.replace(' ', '')
            if ward_code not in code_to_area:
                ward_area = Area.objects.get(
                    country__code='N', type__code='LGW', codes__type='ons', codes__code=ward_code
                )
                code_to_area[ward_code] = ward_area

            if parl_code not in code_to_area and len(parl_code)==3: # Ignore Derryaghy line
                parl_area = Area.objects.get(
                    country__code='N', type__code='WMC', codes__type='ons', codes__code=parl_code,
                )
                gss_code = parl_area.all_codes['gss']
                # Store lookup for both old and new codes, so any version of NSPD will work
                code_to_area[parl_code] = parl_area
                code_to_area[gss_code] = parl_area
                nia_area = Area.objects.get(
                    country__code='N', type__code='NIE', names__type='S', names__name=parl_name,
                )
                code_to_area['NIE' + parl_code] = nia_area
                code_to_area['NIE' + gss_code] = nia_area

        count = { 'total': 0, 'updated': 0, 'unchanged': 0, 'created': 0 }
        for row in csv.reader(open(file)):
            if row[4]: continue # Terminated postcode
            if row[11] == '9': continue # PO Box etc.

            postcode = row[0].strip().replace(' ', '')
            if postcode[0:2] != 'BT': continue # Only importing NI from NSPD

            # NSPD (now ONSPD) started using GSS codes for Parliament in February 2011
            # Detect this here; although they're still using old codes for council/wards
            gss = True if len(row[7]) == 6 else False

            # Create/update the postcode
            location = Point(map(float, row[9:11]), srid=29902) # Irish Grid SRID
            try:
                pc = Postcode.objects.get(postcode=postcode)
                pc_location = pc.as_irish_grid()
                if round(pc_location[0]) != location[0] or round(pc_location[1]) != location[1]:
                    pc.location = location
                    pc.save()
                    count['updated'] += 1
                else:
                    count['unchanged'] += 1
            except Postcode.DoesNotExist:
                pc = Postcode.objects.create(postcode=postcode, location=location)
                count['created'] += 1

            # Create/update the areas
            if gss:
                ons_code = row[7].replace(' ', '')
                parl_code = row[17]
            else:
                ons_code = ''.join(row[5:8])
                parl_code = row[17].replace('N', '7')
            output_area = row[33]
            super_output_area = row[44]

            ward = code_to_area[ons_code]
            electoral_area = ward.parent_area
            council = electoral_area.parent_area
            nia_area = code_to_area['NIE' + parl_code]
            parl_area = code_to_area[parl_code]

            pc.areas.clear()
            pc.areas.add(ward, electoral_area, council, nia_area, parl_area, euro_area)
            transaction.commit()

            count['total'] += 1
            if count['total'] % 10000 == 0:
                print "Imported %d (%d new, %d changed, %d same)" % (
                    count['total'], count['created'], count['updated'], count['unchanged']
                )

