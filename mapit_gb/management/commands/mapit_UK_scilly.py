# This script is used to fix up the Isles of Scilly, as Boundary-Line only contains
# the Isles alone. We have to generate the COP parishes within it.

from __future__ import print_function

import csv
import re
from django.core.management.base import LabelCommand
from mapit.models import Postcode, Area, Country, Type, CodeType, NameType


class Command(LabelCommand):
    help = 'Sort out the Isles of Scilly'
    args = '<Code-Point Open TR file> or <ONSPD CSV file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--allow-terminated-postcodes',
            action='store_true',
            dest='include-terminated',
            default=False,
            help=('Set if you want to fix wards for terminated postcodes (only '
                  'relevant for ONSPD files, Code-Point Open contains no '
                  'terminated postcodes)')
        )
        parser.add_argument(
            '--allow-no-location-postcodes',
            action='store_true',
            dest='include-no-location',
            default=False,
            help=('Set if you want to fix wards for postcodes with no location '
                  '(quality 9 in ONSPD, quality 90 in Code Point Open)')
        )

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
                country=Country.objects.get(code='E'),
                type=Type.objects.get(code='COP'),
                code_type='gss',
                code=new_ward_code
            )
            area.names.get_or_create(type=NameType.objects.get(code='S'), name=ward_name)
            area.codes.get_or_create(type=CodeType.objects.get(code='ons'), code=old_ward_code)
            if area.parent_area != council:
                area.parent_area = council
                area.save()
            ward[old_ward_code] = area
            ward[new_ward_code] = area

        for row in csv.reader(open(file)):
            postcode, ward_code, lacks_location, terminated = self.extract_data(row)
            if postcode[0:2] not in ('TR'):
                continue  # Ignore non scilly postcodes
            if ward_code is None:
                continue  # Ignore if we couldn't extract a scilly ward_code
            if terminated and not options['include-terminated']:
                continue  # Ignore terminated postcodes
            if lacks_location and not options['include-no-location']:
                continue  # Ignore postcodes without a known location

            pc = Postcode.objects.get(postcode=postcode)
            pc.areas.add(ward[ward_code])
            print(".", end=' ')

    def extract_data(self, row):
        postcode = row[0].strip().replace(' ', '')
        if len(row) == 10:  # Post Aug 2011 Code-Point Open file
            ward_code = row[9] if self.is_scilly_gss_code(row[9]) else None
            lacks_location = row[1] == '90'
            terminated = False
        elif len(row) == 19:  # Pre-Aug 2011 Code-Point Open file
            code = ''.join(row[15:18])
            ward_code = code if self.is_scilly_ons_code(code) else None
            lacks_location = row[1] == '90'
            terminated = False
        else:  # ONSPD file
            ward_code = row[7] if self.is_scilly_gss_code(row[7]) else None
            lacks_location = row[11] == '9'
            terminated = row[4]
        return (postcode, ward_code, lacks_location, terminated)

    def is_scilly_gss_code(self, gss_code):
        return re.match('^E0500832[2-6]$', gss_code)

    def is_scilly_ons_code(self, ons_code):
        return ons_code[0:4] == '00HF'
