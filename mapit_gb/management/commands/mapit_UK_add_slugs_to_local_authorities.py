# This script is for a one off import of govuk slugs for local authorities

import json
import os.path

from django.core.management.base import BaseCommand
from mapit.models import Area, CodeType


class Command(BaseCommand):
    help = 'Assigns slugs from authorities.json to local authorities'

    def handle(self, *args, **options):
        code_type, _ = CodeType.objects.get_or_create(
            code='govuk_slug',
            defaults={'description': 'Slug for use by GOV.UK'}
        )

        file_path = os.path.join(os.path.dirname(__file__), '../../data/authorities.json')

        with open(file_path) as f:
            authorities = json.load(f)

        for slug, authority_details in authorities.items():
            gss_code = authority_details['gss']
            if gss_code:
                try:
                    area = Area.objects.get(codes__code=gss_code, codes__type__code='gss')
                    area.codes.update_or_create(type=code_type, defaults={'code': slug})

                except Area.DoesNotExist:
                    # An area that existed at the time of the mapping, but no longer
                    print 'Area for {authority} {gss_code} not found'.format(
                        authority=slug,
                        gss_code=gss_code
                    )
