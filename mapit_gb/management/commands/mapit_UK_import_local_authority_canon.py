# coding=UTF-8
# This script is used to import codes from the various registers of local
# authority names. The lookup is stored at:
# https://raw.githubusercontent.com/ajparsons/uk_local_authority_names_and_codes/master/lookup_gss_to_registry.csv

from __future__ import print_function

import csv

from django.core.management.base import LabelCommand

from mapit.models import CodeType, Code


class Command(LabelCommand):
    """
    Source file is https://github.com/ajparsons/uk_local_authority_names_and_codes
    lookup_gss_to_registry.csv
    """
    help = 'Import local authority register codes for existing gss codes'
    label = '<GSS to Registry Code CSV File>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true',
                            dest='commit', help='Actually update the database')

    def handle_label(self, filename, **options):
        # Add the CodeType
        if options['commit']:
            code_type, _ = CodeType.objects.update_or_create(
                code='local-authority-canonical',
                defaults={
                    'description': "Canonical authority codes for England, Scotland, Wales and Northern Ireland"
                }
            )
        else:
            code_type = CodeType(code='local-authority-canonical')

        # Add Codes
        data_file = csv.DictReader(open(filename))
        for line in data_file:
            try:
                gss_code = Code.objects.get(code=line['gss-code'], type__code='gss')
            except Code.DoesNotExist:
                print("Unknown code {} for '{}' (may be old GSS code for area)".format(
                    line['gss-code'], line['local-authority-code']), file=self.stderr)
                continue

            if options['commit']:
                Code.objects.get_or_create(
                    code=line['local-authority-code'],
                    type=code_type,
                    area=gss_code.area
                )
