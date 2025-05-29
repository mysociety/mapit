# This script activates the currently inactive generation.

from django.core.management.base import BaseCommand, CommandError
from mapit.models import Generation


class Command(BaseCommand):
    help = 'Actives the inactive generation'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        new = Generation.objects.new()
        if not new:
            raise CommandError("You do not have an inactive generation to activate")

        new.active = True
        if options['commit']:
            new.save()
            self.stdout.write("%s - activated" % new)
        else:
            self.stdout.write("%s - not activated, dry run" % new)
