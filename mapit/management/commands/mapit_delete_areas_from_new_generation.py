# This script deletes all the areas from the new generation (i.e. the
# most recent inactive one).

from __future__ import print_function

from django.core.management.base import BaseCommand, CommandError
from mapit.models import Generation, Area


class Command(BaseCommand):
    help = 'Remove all areas from the new (inactive) generation'
    args = '<GENERATION-ID>'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        new = Generation.objects.new()
        if not new:
            raise CommandError("There's no new inactive generation to delete areas from")

        generations = list(Generation.objects.all().order_by('id'))
        if len(generations) <= 1:
            previous_generation = None
        else:
            previous_generation = generations[-2]

        for area in Area.objects.filter(generation_low__lte=new, generation_high__gte=new):

            print("Considering", area)

            g_low = area.generation_low
            g_high = area.generation_high

            if g_low not in generations:
                raise Exception("area.generation_low was " + g_low + ", which no longer exists!")
            if g_high not in generations:
                raise Exception("area.generation_high was " + g_high + ", which no longer exists!")

            if area.generation_low == new and area.generation_high == new:
                print("  ... only exists in", new, "so will delete")
                if options['commit']:
                    area.delete()
                    print("  ... deleted.")
                else:
                    print("  ... not deleting, since --commit wasn't specified")
            elif area.generation_low.id < new.id and area.generation_high == new:
                print(
                    "  ... still exists in an earlier generation, so lowering generation_high to",
                    previous_generation)
                area.generation_high = previous_generation
                if options['commit']:
                    area.save()
                    print("  ... lowered.")
                else:
                    print("  ... not lowering, since --commit wasn't specified")

            elif area.generation_high.id > new.id:
                # This should never happen - it'd mean the
                # implementation of Generation.objects.new() has
                # changed or something else is badly wrong:
                message = "Somehow area.generation_high (" + \
                    str(area.generation_high) + \
                    ") is after Generation.objects.new() (" + \
                    str(new) + ")"
                raise Exception(message)
