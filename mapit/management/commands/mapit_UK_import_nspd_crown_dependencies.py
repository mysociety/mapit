# This script is used to import Crown Dependency postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/

import csv
from mapit.management.commands.mapit_import_postal_codes import Command

class Command(Command):
    help = 'Imports Crown Dependency postcodes from the NSPD'
    args = '<NSPD CSV file>'
    option_defaults = { 'strip': True, 'no-location': True }

    def pre_row(self, row, options):
        if row[4]: return False # Terminated postcode
        if self.code[0:2] not in ('GY', 'JE', 'IM'): return False # Only importing Crown dependencies from NSPD
        return True
