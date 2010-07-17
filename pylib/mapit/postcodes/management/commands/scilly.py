# This script is used to fix up the Isles of Scilly, as Boundary-Line only contains
# the Isles alone. We have to generate the COP parishes within it.

import csv
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
from mapit.postcodes.models import Postcode
from mapit.areas.models import Area, Generation

class Command(LabelCommand):
    help = 'Sort out the Isles of Scilly'
    args = '<Code-Point Open TR file>'

    def handle_label(self, file, **options):
        council = Area.objects.get(codes__type='ons', codes__code='00HF')
        if council.type != 'COI':
            council.type = 'COI'
            council.save()
        
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
            if area.parent_area != council:
                area.parent_area = council
                area.save()
            ward[ward_code] = area

        for row in csv.reader(open(file)):
            if row[1] == '90': continue
            postcode = row[0].strip().replace(' ', '')
            ons_code = ''.join(row[15:18])
            if ons_code[0:4] != '00HF': continue
            pc = Postcode.objects.get(postcode=postcode)
            pc.areas.add(ward[ons_code])

