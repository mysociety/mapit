# This script is used to create a new inactive generation for
# inputting new boundaries of some sort.

from django.core.management.base import BaseCommand, CommandError
from mapit.models import Generation


class Command(BaseCommand):
    help = 'Create a new generation'

    def add_arguments(self, parser):
        parser.add_argument('--desc', action='store', dest='desc', help='Description of this generation')
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        new_generation = Generation.objects.new()
        if new_generation:
            raise CommandError("You already have an inactive generation")

        if not options['desc']:
            raise CommandError("You must specify a generation description")

        g = Generation(description=options['desc'])
        self.stdout.write("Creating generation...")
        if options['commit']:
            g.save()
            self.stdout.write("...saved: %s" % g)
        else:
            self.stdout.write("...not saving, dry run")
