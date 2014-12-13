# A simple script for timing point-in-polygon lookups in an instance
# of MapIt UK.  The results for this tend to be quite variable - the
# suggestion in the timeit documentation is to take the minimum over
# a number of repetitions.

from random import randint, uniform  # seed
# from time import time
from timeit import repeat  # timeit, Timer
from django.core.management.base import BaseCommand, CommandError
# from django.db import connection
from django.db.models import Min, Max
from mapit.models import Postcode

minimum_postcode_id = Postcode.objects.aggregate(Min('id'))['id__min']
maximum_postcode_id = Postcode.objects.aggregate(Max('id'))['id__max']


def get_random_UK_location():
    """Return a random location generally on the UK mainland

    This doesn't need to be very good for our testing purposes, so we
    just pick a random postcode from the database, and add some error
    to the latitude and longitude for that postcode.  Sometimes this
    might give you a point which is actually out in the sea, but again
    this doesn't really matter for these purposes.  Obviously these
    locations aren't going to be uniform across the UK, since
    postcodes are more dense in towns."""

    location = None
    while not location:
        postcode_id = randint(minimum_postcode_id, maximum_postcode_id)
        try:
            location = Postcode.objects.get(id=postcode_id).location
        # It's always possible that the IDs aren't sequential:
        except Postcode.DoesNotExist:
            continue

    # This is (very) roughly a kilometer in degrees longitude or
    # latitude in the UK:
    max_error_to_add = 0.01
    new_lon = location.coords[0] + uniform(-max_error_to_add, max_error_to_add)
    new_lat = location.coords[1] + uniform(-max_error_to_add, max_error_to_add)
    location.coords = (new_lon, new_lat)
    return location

random_locations = None


class Command(BaseCommand):
    args = '<iterations>'
    help = 'Time many point-in-polygon lookups'

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError('There must be only one argument')

        try:
            iterations = int(args[0])
        except ValueError:
            raise CommandError('The iterations argument must be an integer')

        repeats = 5

        # So that the time to generate random locations isn't a factor
        # in the timing, generate all the locations ahead of time.
        # (In fact, this takes a vanishingly small amount of time
        # compared to the area lookups in the current version, but in
        # previous versions of this script generating random locations
        # was much slower.)

        to_generate = repeats * iterations
        print("Generating %d random locations in the UK ..." % (to_generate,))
        global random_locations
        random_locations = [get_random_UK_location() for _ in range(to_generate)]
        print("... done.")

        # Now look up each of those locations, timing the process with
        # timeit.  Note that the list() is required to cause
        # evaluation of the GeoQuerySet.

        print("Testing point-in-polygon tests ...")
        result = repeat(stmt='list(Area.objects.by_location(random_locations.pop()))',
                        setup='''
from mapit.models import Area
from mapit.management.commands.mapit_UK_time_lookups import random_locations
''',
                        repeat=repeats,
                        number=iterations)
        print("... done.")

        print(result)
