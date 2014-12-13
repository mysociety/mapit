# This script activates the currently inactive generation.

from optparse import make_option
from django.core.management.base import NoArgsCommand
from mapit.models import Generation


class Command(NoArgsCommand):
    help = 'Actives the inactive generation'
    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle(self, **options):
        new = Generation.objects.new()
        if not new:
            raise Exception("You do not have an inactive generation to activate")

        new.active = True
        if options['commit']:
            new.save()
            print("%s - activated" % new)
        else:
            print("%s - not activated, dry run" % new)
