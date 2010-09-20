# This script is used to import Crown Dependency postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/

import csv
from django.core.management.base import LabelCommand
from mapit.postcodes.models import Postcode

class Command(LabelCommand):
    help = 'Imports Crown Dependency postcodes from the NSPD'
    args = '<NSPD CSV file>'

    def handle_label(self, file, **options):
        count = { 'total': 0, 'exists': 0, 'created': 0 }
        for row in csv.reader(open(file)):
            if row[4]: continue # Terminated postcode

            postcode = row[0].strip().replace(' ', '')
            if postcode[0:2] not in ('GY', 'JE', 'IM'): continue # Only importing Crown dependencies from NSPD

            # Create/update the postcode
            try:
                pc = Postcode.objects.get(postcode=postcode)
                count['exists'] += 1
            except Postcode.DoesNotExist:
                pc = Postcode.objects.create(postcode=postcode)
                count['created'] += 1

            count['total'] += 1
            if count['total'] % 1000 == 0:
                print "Imported %d (%d new, %d already there)" % (
                    count['total'], count['created'], count['exists']
                )

