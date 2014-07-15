# This script is used to fix up the Isles of Scilly, as Boundary-Line only contains
# the Isles alone. We have to generate the COP parishes within it.

import csv
import re
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
from mapit.models import Postcode, Area, Generation, Country, Type, CodeType, NameType

class Command(LabelCommand):
    help = 'Sort out the Isles of Scilly'
    args = '<Code-Point Open TR file>'

    def handle_label(self, file, **options):
        # The Isles of Scilly have changed their code in B-L, but Code-Point still has the old code currently
        try:
            council = Area.objects.get(codes__type__code='gss', codes__code='E06000053')
        except:
            council = Area.objects.get(codes__type__code='ons', codes__code='00HF')
        if council.type != Type.objects.get(code='COI'):
            council.type = Type.objects.get(code='COI')
            council.save()
        
        wards = (
            ('00HFMA', 'E05008322', 'Bryher'),
            ('00HFMB', 'E05008323', 'St. Agnes'),
            ('00HFMC', 'E05008324', "St. Martin's"),
            ('00HFMD', 'E05008325', "St. Mary's"),
            ('00HFME', 'E05008326', 'Tresco'),
        )
        ward = {}
        for old_ward_code, new_ward_code, ward_name in wards:
            area = Area.objects.get_or_create_with_code(
                country=Country.objects.get(code='E'), type=Type.objects.get(code='COP'), code_type='gss', code=new_ward_code
            )
            area.names.get_or_create(type=NameType.objects.get(code='S'), name=ward_name)
            area.codes.get_or_create(type=CodeType.objects.get(code='ons'), code=old_ward_code)
            if area.parent_area != council:
                area.parent_area = council
                area.save()
            ward[old_ward_code] = area
            ward[new_ward_code] = area

        for row in csv.reader(open(file)):
            if row[1] == '90': continue
            postcode = row[0].strip().replace(' ', '')
            if len(row) == 10:
                ons_code = row[9]
                if not re.match('^E0500832[2-6]$', ons_code): continue
            else:
                ons_code = ''.join(row[15:18])
                if ons_code[0:4] != '00HF': continue
            pc = Postcode.objects.get(postcode=postcode)
            pc.areas.add(ward[ons_code])
            print ".",
