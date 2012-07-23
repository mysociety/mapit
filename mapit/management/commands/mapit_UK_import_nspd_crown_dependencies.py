# This script is used to import Crown Dependency postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/

import csv
from mapit.management.command_utils import PostcodeCommand

class Command(PostcodeCommand):
    help = 'Imports Crown Dependency postcodes from the NSPD'
    args = '<NSPD CSV file>'
    often = 1000

    def handle_label(self, file, **options):
        for row in csv.reader(open(file)):
            if row[4]: continue # Terminated postcode

            postcode = row[0].strip().replace(' ', '')
            if postcode[0:2] not in ('GY', 'JE', 'IM'): continue # Only importing Crown dependencies from NSPD

            self.do_postcode(postcode, None)
        self.print_stats()
