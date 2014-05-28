# This script is to be run as a one-off to fix up a specific boundary that
# the Ordnance survey gave the wrong code too in the 2013-10 edition of the
# boundary line. It must be run *before* importing the 2014-05 edition.

from optparse import make_option
from django.core.management.base import NoArgsCommand
from django.contrib.gis.gdal import *
from mapit.models import Area, CodeType

class Command(NoArgsCommand):
    help = 'Fix the GSS code of UTE South Tynedale so that we can import the May 2014 boundary line'
    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle_noargs(self, **options):
        code_version = CodeType.objects.get(code='gss')

        # We need to remove the code E05009154 from the South Tynedale area
        # (which lived in MapIt UK's database from generations 1 - 20)
        # so that when we add it back in during the May 2014 import
        # (MapIt UK's generation 22), we don't get an  error from the
        # boundary-line import script. Only one area should have this code at
        # any given time, they can't both share it.
        area = Area.objects.get(codes__code='E05009154', codes__type=code_version)
        if options['commit']:
            area.codes.get(code='E05009154', type=code_version).delete()