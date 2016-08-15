# This script is for a one off import of all the new GSS codes.

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
        mapping = csv.reader(open('../data/BL-2010-10-code-change.csv'))
        next(mapping)
        for row in mapping:
            new_code, name, old_code = row[0], row[1], row[3]
            try:
                area = Area.objects.get(codes__code=old_code, codes__type__code='ons')
            except Area.MultipleObjectsReturned:
                if old_code == '11' or old_code == '12':
                    # Also the IDs of two EURs, but they're not in this lookup
                    area = Area.objects.get(type__code='CTY', codes__code=old_code, codes__type__code='ons')
                elif old_code == '09':
                    # Also the ID of a now non-existent county council
                    area = Area.objects.get(type__code='EUR', codes__code=old_code, codes__type__code='ons')
                else:
                    raise
            except Area.DoesNotExist:
                # Don't have old WMC codes in, go on name
                try:
                    area = Area.objects.get(
                        type__code='WMC', name=name.decode('iso-8859-1'), generation_high=current_generation)
                except:
                    # New parishes in 2010-01
                    # 00NS007 Caldey Island and St. Margaret's Island
                    # 00PK027 Risca East
                    # 00PK028 Risca West
                    # 18UK064 Area not comprised in any Parish-Lundy Island
                    # 19UG029 Affpuddle and Turnerspuddle
                    continue

            # Check if already has the right code
            if 'gss' in area.all_codes and area.all_codes['gss'] == new_code:
                continue

            try:
                area.codes.create(type=CodeType.objects.get(code='gss'), code=new_code)
            except IntegrityError:
                raise Exception("Key already exists for %s, can't give it %s" % (area, new_code))
