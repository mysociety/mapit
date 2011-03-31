# This script is used to create a new inactive generation for
# inputting new boundaries of some sort.

from optparse import make_option
from django.core.management.base import NoArgsCommand
from mapit.areas.models import Generation

class Command(NoArgsCommand):
    help = 'Create a new generation'
    option_list = NoArgsCommand.option_list + (
        make_option('--desc', action='store', dest='desc', help='Description of this generaiton'),
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle(self, **options):
        new_generation = Generation.objects.new()
        if new_generation:
            raise Exception, "You already have an inactive generation"

        if not options['desc']:
            raise Exception, "You must specify a generation description"

        g = Generation(description=options['desc'])
        print "Creating generation..."
        if options['commit']:
            g.save()
            print "...saved: %s" % g
        else:
            print "...not saving, dry run"
