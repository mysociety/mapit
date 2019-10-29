# This script is to be run as a one-off after an import of the original, buggy,
# May 2019 OS Boundary-Line, in order to fix another issue with it that I
# missed in the previous script. It needs to be run before importing the
# October 2019 edition on top.

from __future__ import print_function

from django.core.management.base import BaseCommand
from mapit.models import Code, CodeType


class Command(BaseCommand):
    help = 'Fix another issue with May 2019 OS Boundary-Line'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        code_version = CodeType.objects.get(code='gss')

        # We need to remove the code E04003492 from the Abbotsbury area (which
        # lived in MapIt UK's database from generations 12-35) and rename the
        # bad code (generation 36) to it. Only one area should have this code
        # at any given time, they can't both share it.
        old = 'E0400349'
        new = 'E04003492'
        code = Code.objects.get(type=code_version, code=new)
        print('Deleting code %s' % (new,))
        if options['commit']:
            code.delete()

        code = Code.objects.get(type=code_version, code=old)
        code.code = new
        print('Updating area %s to %s' % (old, new))
        if options['commit']:
            code.save()
