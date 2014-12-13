# This script is used to import National Park postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/
#
# Just as an example, haven't actually run this.
#
# The fields of NSPD Open CSV file are:
#   0: Postcode (7), 36: National Park

import csv
from django.core.management.base import LabelCommand
from mapit.models import Postcode, Area, Generation, Type

lookup = {
    '01': 'Dartmoor National Park',
    '02': 'Exmoor National Park',
    '03': 'Lake District National Park',
    '04': 'Northumberland National Park',
    '05': 'North York Moors National Park',
    '06': 'Peak District National Park',
    '07': 'The Broads Authority',
    '08': 'Yorkshire Dales National Park',
    '09': 'Brecon Beacons National Park',
    '10': 'Pembrokeshire Coast National Park',
    '11': 'Snowdonia National Park',
    '12': 'New Forest National Park',
    '14': 'The Cairngorms National Park',
    '15': 'The Loch Lomond and the Trossachs National Park',
    '16': 'South Downs National Park',
}


class Command(LabelCommand):
    help = 'Imports postcode->National Park from the NSPD, creates the areas if need be'
    args = '<NSPD CSV file>'

    def handle_label(self, file, **options):
        if not Generation.objects.new():
            raise Exception("No new generation to be used for import!")

        count = 0
        for row in csv.reader(open(file)):
            if row[4]:
                continue  # Terminated postcode
            if row[11] == '9':
                continue  # PO Box etc.

            postcode = row[0].strip().replace(' ', '')

            try:
                pc = Postcode.objects.get(postcode=postcode)
            except Postcode.DoesNotExist:
                continue  # Ignore postcodes that aren't already in db

            national_park = row[36]
            name = lookup[national_park]
            national_park_area = Area.objects.get_or_create_with_name(
                type=Type.objects.get(code='NPK'), name_type='S', name=name)
            pc.areas.add(national_park_area)

            count += 1
            if count % 10000 == 0:
                print("Imported %d" % count)
