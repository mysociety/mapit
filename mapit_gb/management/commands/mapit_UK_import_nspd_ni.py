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
import os.path
from mapit.models import Area
from mapit.management.commands.mapit_import_postal_codes import Command


class Command(Command):
    help = 'Imports Northern Ireland postcodes from the NSPD, using existing areas only'
    args = '<NSPD CSV file>'
    option_defaults = {'strip': True, 'srid': 29902, 'coord-field-lon': 10, 'coord-field-lat': 11}

    def handle_label(self, file, **options):
        # First set up the areas needed (as we have to match to postcode manually)
        self.euro_area = Area.objects.get(country__code='N', type__code='EUR')

        # Read in new ONS code to names, look up existing wards and Parliamentary constituencies
        snac = csv.reader(open(os.path.dirname(__file__) + '/../../data/snac-2009-ni-cons2ward.csv'))
        next(snac)
        code_to_area = {}
        for parl_code, parl_name, ward_code, ward_name, district_code, district_name in snac:
            ward_code = ward_code.replace(' ', '')
            if ward_code not in code_to_area:
                ward_area = Area.objects.get(
                    country__code='N', type__code='LGW', codes__type__code='ons', codes__code=ward_code
                )
                code_to_area[ward_code] = ward_area

            if parl_code not in code_to_area and len(parl_code) == 3:  # Ignore Derryaghy line
                parl_area = Area.objects.get(
                    country__code='N', type__code='WMC', codes__type__code='ons', codes__code=parl_code,
                )
                gss_code = parl_area.all_codes['gss']
                # Store lookup for both old and new codes, so any version of NSPD will work
                code_to_area[parl_code] = parl_area
                code_to_area[gss_code] = parl_area
                nia_area = Area.objects.get(
                    country__code='N', type__code='NIE', names__type__code='S', names__name=parl_name,
                )
                code_to_area['NIE' + parl_code] = nia_area
                code_to_area['NIE' + gss_code] = nia_area
        self.code_to_area = code_to_area

        # Start the main import process
        self.process(file, options)

    def pre_row(self, row, options):
        if row[4]:
            return False  # Terminated postcode
        if row[11] == '9':
            return False  # PO Box etc.
        if self.code[0:2] != 'BT':
            return False  # Only importing NI from NSPD

        # NSPD (now ONSPD) started using GSS codes for Parliament in February 2011
        # Detect this here; although they're still using old codes for council/wards
        gss = True if len(row[7]) == 6 else False

        # Create/update the areas
        if gss:
            ons_code = row[7].replace(' ', '')
            parl_code = row[17]
        else:
            ons_code = ''.join(row[5:8])
            parl_code = row[17].replace('N', '7')
        # output_area = row[33]
        # super_output_area = row[44]

        ward = self.code_to_area[ons_code]
        electoral_area = ward.parent_area
        self.areas = [
            ward,
            electoral_area,
            electoral_area.parent_area,  # Council
            self.code_to_area['NIE' + parl_code],  # Assembly
            self.code_to_area[parl_code],  # Parliament
            self.euro_area,
        ]

        return True

    def post_row(self, pc):
        pc.areas.clear()
        pc.areas.add(*self.areas)
