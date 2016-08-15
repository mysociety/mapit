# This script activates the currently inactive generation.

from django.core.management.base import BaseCommand
from mapit.models import Generation


class Command(BaseCommand):
    help = 'Actives the inactive generation'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

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
