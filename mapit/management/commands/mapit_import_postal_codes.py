# This is a generic script for importing postal codes in some format from a CSV
# file. The CSV file should have the following columns:
#   Postal code, Latitude, Longitude
# By default in those positions, though you can specify other column numbers on
# the command line

import csv
from django.db import transaction
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
from django.conf import settings
from mapit.models import Postcode


class Command(LabelCommand):
    help = 'Import Postal codes from a CSV file or files'
    args = '<CSV files>'
    count = {'total': 0, 'updated': 0, 'unchanged': 0, 'created': 0}
    often = 1000

    option_defaults = {}

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--code-field',
            action='store',
            dest='code-field',
            default=1,
            help='The column of the CSV containing the postal code (default 1, first)'
        )
        parser.add_argument(
            '--coord-field-lat',
            action='store',
            dest='coord-field-lat',
            default=2,
            help='The column of the CSV containing the lat/y co-ordinate (default 2)'
        )
        parser.add_argument(
            '--coord-field-lon',
            action='store',
            dest='coord-field-lon',
            default=None,
            help='The column of the CSV containing the lon/x co-ordinate (default --coord-field-lat + 1)'
        )
        parser.add_argument(
            '--header-row',
            action='store_true',
            dest='header-row',
            default=False,
            help='Set if the CSV file has a header row'
        )
        parser.add_argument(
            '--no-location',
            action="store_false",
            dest='location',
            default=True,
            help='Set if the postal codes have no associated location (still useful for existence checks)'
        )
        parser.add_argument(
            '--srid',
            action="store",
            dest='srid',
            default=4326,
            help='The SRID of the projection for the data given (default 4326 WGS-84)'
        )
        parser.add_argument(
            '--strip',
            action="store_true",
            dest='strip',
            default=False,
            help='Whether to strip all spaces from the postal code before import'
        )
        parser.add_argument(
            '--tabs',
            action="store_true",
            dest='tabs',
            default=False,
            help='If the CSV file actually uses tab as its separator'
        )

    def handle_label(self, file, **options):
        self.process(file, options)

    def process(self, file, options):
        options.update(self.option_defaults)
        if options['tabs']:
            reader = csv.reader(open(file), dialect='excel-tab')
        else:
            reader = csv.reader(open(file))
        if options['header-row']:
            next(reader)
        for row in reader:
            self._process_row(row, options)
        self.print_stats()

    @transaction.atomic
    def _process_row(self, row, options):
        self.code = row[int(options['code-field']) - 1].strip()
        if options['strip']:
            self.code = self.code.replace(' ', '')
        if self.pre_row(row, options):
            pc = self.handle_row(row, options)
            self.post_row(pc)

    def pre_row(self, row, options):
        return True

    def post_row(self, pc):
        return True

    def location_available_for_row(self, row):
        return True

    def handle_row(self, row, options):
        if not options['location'] or not self.location_available_for_row(row):
            return self.do_postcode()

        if not options['coord-field-lon']:
            options['coord-field-lon'] = int(options['coord-field-lat']) + 1
        lat = float(row[int(options['coord-field-lat']) - 1])
        lon = float(row[int(options['coord-field-lon']) - 1])
        srid = int(options['srid'])
        location = Point(lon, lat, srid=srid)
        return self.do_postcode(location, srid)

    # Want to compare co-ordinates so can't use straightforward
    # update_or_create
    def do_postcode(self, location=None, srid=None):
        try:
            pc = Postcode.objects.get(postcode=self.code)
            if location:
                if pc.location:
                    curr_location = (pc.location[0], pc.location[1])
                    if settings.MAPIT_COUNTRY == 'GB':
                        if pc.postcode[0:2] == 'BT':
                            curr_location = pc.as_irish_grid()
                        else:
                            pc.location.transform(27700)  # Postcode locations are stored as WGS84
                            curr_location = (pc.location[0], pc.location[1])
                        curr_location = tuple(map(round, curr_location))
                    elif srid != 4326:
                        pc.location.transform(srid)  # Postcode locations are stored as WGS84
                        curr_location = (pc.location[0], pc.location[1])
                    if curr_location[0] != location[0] or curr_location[1] != location[1]:
                        pc.location = location
                        pc.save()
                        self.count['updated'] += 1
                    else:
                        self.count['unchanged'] += 1
                else:
                    pc.location = location
                    pc.save()
                    self.count['updated'] += 1
            else:
                self.count['unchanged'] += 1
        except Postcode.DoesNotExist:
            pc = Postcode.objects.create(postcode=self.code, location=location)
            self.count['created'] += 1
        self.count['total'] += 1
        if self.count['total'] % self.often == 0:
            self.print_stats()
        return pc

    def print_stats(self):
        print("Imported %d (%d new, %d changed, %d same)" % (
            self.count['total'], self.count['created'],
            self.count['updated'], self.count['unchanged']
        ))
