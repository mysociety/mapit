# This script is used to fix up the Isles of Scilly, as Boundary-Line only contains
# the Isles alone. We have to generate the COP parishes within it.

import csv
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
from mapit.postcodes.models import Postcode
from mapit.areas.models import Area, Generation

class Command(LabelCommand):
    def handle_label(self, file, **options):
        new_generation = Generation.objects.new()
        council = Area.objects.get(codes__type='ons', codes__code='00HF')
        if council.type != 'COI':
            council.type = 'COI'
        council.generation_high = new_generation
        council.save()
        euro = Area.objects.get(names__type='O', names__name='South West Euro Region')
        parl = Area.objects.get(names__type='O', names__name='St. Ives Co Const')
        
        wards = {
            '00HFMA': 'Bryher',
            '00HFMB': 'St. Agnes',
            '00HFMC': "St. Martin's",
            '00HFMD': "St. Mary's",
            '00HFME': 'Tresco',
        }
        ward = {}
        for ward_code, ward_name in wards.items():
            area = Area.objects.get_or_create_with_code(
                country='E', type='COP', code_type='ons', code=ward_code
            )
            area.names.get_or_create(type='S', name=ward_name)
            ward[ward_code] = ward_area

        for row in csv.reader(open(file)):
            if row[1] == '90': continue
            postcode = row[0].strip().replace(' ', '')
            ons_code = ''.join(row[15:18])

            # Create/update the postcode
            location = Point(map(float, row[10:12]), srid=27700)
            try:
                pc = Postcode.objects.get(postcode=postcode)
                if pc.location != location:
                    pc.location = location
                    pc.save()
            except Postcode.DoesNotExist:
                pc = Postcode.objects.create(postcode=postcode, location=location)

            pc.areas.add(euro, parl, council, ward[ons_code])

