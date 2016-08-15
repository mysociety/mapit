# This script deactivates a particular generation

from django.core.management.base import BaseCommand, CommandError
from mapit.models import Generation


class Command(BaseCommand):
    help = 'Deactivate a generation'
    args = '<GENERATION-ID>'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')
        parser.add_argument('--force', action='store_true', dest='force',
                            help='Force deactivation, even if it would leave no active generations')

    def handle(self, generation_id, **options):
        generation_to_deactivate = Generation.objects.get(id=int(generation_id, 10))
        if not generation_to_deactivate.active:
            raise CommandError("The generation %s wasn't active" % (generation_id,))
        active_generations = Generation.objects.filter(active=True).count()
        if active_generations <= 1 and not options['force']:
            raise CommandError(
                "You're trying to deactivate the only active generation. "
                "If this is what you intended, please re-run the command with --force")
        generation_to_deactivate.active = False
        if options['commit']:
            generation_to_deactivate.save()
            print("%s - deactivated" % generation_to_deactivate)
        else:
            print("%s - not deactivated, dry run" % generation_to_deactivate)
