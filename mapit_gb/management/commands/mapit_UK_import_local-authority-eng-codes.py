# coding=UTF-8
# This script is used to import codes from the 'local-authority-eng'
# register at https://local-authority-eng.register.gov.uk/. The actual mapping
# between existing GSS codes and register IDs is in a 'mapping' file at
# https://github.com/openregister/local-authority-data/blob/master/maps/gss.tsv
# and cached in the mapit_gb/data directory.

from __future__ import print_function

import csv
import os

from django.core.management.base import BaseCommand

from mapit.models import CodeType, Code


class Command(BaseCommand):
    help = 'Import local-authority-eng codes'

    def handle(self, **options):
        # Add the CodeType
        code_type, _ = CodeType.objects.update_or_create(
            code='local-authority-eng',
            defaults={
                'description': "GOV.UK local-authority-eng codes"
            }
        )

        # Add Codes
        data_path = os.path.abspath(os.path.join(
            __file__,
            '..', '..', '..', 'data',
            'gss-to-local-authority-eng.tsv'))
        data_file = csv.DictReader(open(data_path), delimiter='\t')
        for line in data_file:
            register_code_type, code = line['local-authority'].split(":")
            if register_code_type == 'local-authority-eng':
                try:
                    gss_code = Code.objects.get(code=line['gss'])
                    Code.objects.get_or_create(
                        code=code,
                        type=code_type,
                        area=gss_code.area
                    )
                except Code.DoesNotExist:
                    print("Unknown code {} for '{}'".format(
                        line['gss'], line['name']), file=self.stderr)
