# This script is for a one off import of all the old ONS codes to a MapIt
# containing only the new ones from a modern Boundary-Line.

import codecs
import csv
import os.path
import sys
from django.core.management.base import BaseCommand
from mapit.models import Area, CodeType
from psycopg2 import IntegrityError

python_version = sys.version_info[0]


def open_csv(filename):
    if python_version < 3:
        o = open(filename)
    else:
        o = codecs.open(filename, 'r', 'latin-1')
    mapping = csv.reader(o)
    next(mapping)
    return mapping


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
        for row in open_csv(os.path.join(os.path.dirname(__file__), '../../data/BL-2010-10-code-change.csv')):
            new_code, old_code = row[0], row[3]
            process(new_code, old_code)

        for row in open_csv(os.path.join(os.path.dirname(__file__), '../../data/BL-2010-10-missing-codes.csv')):
            new_code, old_code = row[1], row[2]
            process(new_code, old_code)
