# This script is for a one off import of all the new GSS codes.
# To include the ones not in the file from Ordnance Survey.

import csv
from django.core.management.base import BaseCommand
from mapit.models import Area, Generation, CodeType
from psycopg2 import IntegrityError


class Command(BaseCommand):
    help = 'Inserts all the new GSS codes into mapit'
    args = '<CSV file mapping old to new>'

    def handle(self, **options):
        current_generation = Generation.objects.current()

        # Read in ward name -> electoral area name/area
        mapping = csv.reader(open('../data/BL-2010-10-missing-codes.csv'))
        next(mapping)
        for row in mapping:
            type, new_code, old_code, name = row
            try:
                area = Area.objects.get(type__code=type, codes__code=old_code, codes__type__code='ons')
            except Area.DoesNotExist:
                area = Area.objects.get(
                    type__code=type, name=name.decode('iso-8859-1'), generation_high=current_generation)

            # Check if already has the right code
            if 'gss' in area.all_codes and area.all_codes['gss'] == new_code:
                continue

            try:
                area.codes.create(type=CodeType.objects.get(code='gss'), code=new_code)
            except IntegrityError:
                raise Exception("Key already exists for %s, can't give it %s" % (area, new_code))
