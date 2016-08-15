# This script is for a one off import of all the old ONS codes to a MapIt
# containing only the new ones from a modern Boundary-Line.

import codecs
import csv
import os.path
from django.core.management.base import BaseCommand
from mapit.models import Area, CodeType
from psycopg2 import IntegrityError


def process(new_code, old_code):
    try:
        area = Area.objects.get(codes__code=new_code, codes__type__code='gss')
    except Area.DoesNotExist:
        # An area that existed at the time of the mapping, but no longer
        return

    # Check if already has the right code
    if 'ons' in area.all_codes and area.all_codes['ons'] == old_code:
        return

    try:
        area.codes.create(type=CodeType.objects.get(code='ons'), code=old_code)
    except IntegrityError:
        raise Exception("Key already exists for %s, can't give it %s" % (area, old_code))


class Command(BaseCommand):
    help = 'Inserts the old ONS codes into mapit'

    def handle(self, **options):
        code_changes = codecs.open(os.path.join(
            os.path.dirname(__file__),
            '../../data/BL-2010-10-code-change.csv')
        if python_version < 3:
            mapping = csv.reader(open(code_change_file_path))
        else:
            code_changes = codecs.open(code_change_file_path, 'r', 'latin-1')
            mapping = csv.reader(code_changes)
        next(mapping)
        for row in mapping:
            new_code, old_code = row[0], row[3]
            process(new_code, old_code)

        missing_codes_file_path = os.path.join(
            os.path.dirname(__file__),
            '../../data/BL-2010-10-missing-codes.csv')
        if python_version < 3:
            mapping = csv.reader(open(missing_codes_file_path))
        else:
            missing_codes = codecs.open(missing_codes_file_path, 'r', 'latin-1')
            mapping = csv.reader(missing_codes)
        next(mapping)
        for row in mapping:
            new_code, old_code = row[1], row[2]
            process(new_code, old_code)
