# This script is used to import postcodes from the ONS Postcode Directory:
# https://www.ons.gov.uk/methodology/geography/geographicalproducts/postcodeproducts

import csv
from django.db import connection, transaction
from django.core.management.base import LabelCommand
from mapit.iterables import iterable_to_stream


FIELD_CODE = 0
FIELD_END_DATE = 4
FIELD_COORD_LON = 11
FIELD_COORD_LAT = 12
FIELD_PQI = 13


def strip_spaces(row):
    row[FIELD_CODE] = row[FIELD_CODE].replace(' ', '')
    return row


class Command(LabelCommand):
    help = ('Imports UK postcodes from the ONSPD.\n\nBy default imports only '
            'live GB postcodes with a lat/lng, options are available to also '
            'import terminated, NI, or Crown Dependency postcodes and those '
            'without locations.')
    label = '<ONSPD CSV file>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--allow-terminated-postcodes',
            action='store_true',
            dest='include-terminated',
            default=False,
            help=('Set if you want to import terminated postcodes.  Affects all '
                  'postcodes: GB, NI, and Crown Dependencies')
        )
        parser.add_argument(
            '--allow-no-location-postcodes',
            action='store_true',
            dest='include-no-location',
            default=False,
            help=('Set if you want to import postcodes without location info '
                  '(quality: 9).  Affects GB and NI postcodes only.  Crown '
                  'Dependency postcodes have no location and will be imported '
                  'based on the value of --crown-dependencies, regardless of '
                  'your choice for this option.')
        )
        parser.add_argument(
            '--crown-dependencies',
            action='store',
            dest='crown-dependencies',
            default='exclude',
            help=('How to handle crown dependency postcodes.  Set to "include" '
                  'to import them, set to "exclude" to ignore them, set to '
                  '"only" to import only these. (Default: exclude).  Note that '
                  'Crown Dependency postcodes have no location info and are '
                  'imported solely based on this option, regardless of the '
                  'presence of --allow-no-location-postcodes.')
        )
        parser.add_argument(
            '--northern-ireland',
            action='store',
            dest='northern-ireland',
            default='exclude',
            help=('How to handle Northern Ireland postocdes.  Set to "include" '
                  'to import them, set to "exclude" to ignore them, set to '
                  '"only" to import only these. (Default: exclude).  You should'
                  ' run mapit_UK_import_onspd_ni_areas before trying to import '
                  'any NI postcodes.')
        )

    def handle_label(self, file, **options):
        self.check_options_are_valid(options)

        reader = csv.reader(open(file))
        next(reader)

        reader = filter(lambda row: self.pre_row(row, options), reader)
        reader = map(strip_spaces, reader)
        reader = map(lambda row: f'{row[FIELD_CODE]},{row[FIELD_COORD_LON]},{row[FIELD_COORD_LAT]}\n'.encode(), reader)
        reader = iterable_to_stream(reader)

        with transaction.atomic():
            cursor = connection.cursor()
            self.stdout.write("Creating temporary table")
            cursor.execute('CREATE TEMPORARY TABLE mapit_postcode_new '
                           '(postcode varchar(7), location geometry(Point, 4326), easting int, northing int) '
                           'ON COMMIT DROP')
            self.stdout.write("Copying in data:")
            cursor.copy_expert('COPY mapit_postcode_new(postcode, easting, northing) '
                               'FROM STDIN WITH (FORMAT csv)', reader)
            self.stdout.write(f"{cursor.rowcount} rows")
            self.stdout.write("Setting geometry column")
            cursor.execute("UPDATE mapit_postcode_new "
                           "SET location = ST_Transform(ST_SetSRID(ST_Point(easting, northing), 27700), 4326) "
                           "WHERE postcode NOT LIKE 'BT%'")
            cursor.execute("UPDATE mapit_postcode_new "
                           "SET location = ST_Transform(ST_SetSRID(ST_Point(easting, northing), 29902), 4326) "
                           "WHERE postcode LIKE 'BT%'")
            self.stdout.write("Updating existing rows:")
            cursor.execute('UPDATE mapit_postcode SET location = n.location FROM mapit_postcode_new n '
                           'WHERE (n.location IS DISTINCT FROM mapit_postcode.location) '
                           'AND n.postcode = mapit_postcode.postcode')
            self.stdout.write(f"{cursor.rowcount} rows updated")
            self.stdout.write("Adding new data:")
            cursor.execute('INSERT INTO mapit_postcode (postcode, location) '
                           'SELECT n.postcode, n.location FROM mapit_postcode_new n '
                           'LEFT JOIN mapit_postcode p ON n.postcode = p.postcode WHERE p.postcode IS NULL')
            self.stdout.write(f"{cursor.rowcount} rows created")

    def pre_row(self, row, options):
        if self.reject_row_based_on_termination_data(row, options):
            return False  # Terminated postcode
        elif self.reject_row_based_on_location_data(row, options):
            return False  # go no further unless we want codes with no location
        elif self.reject_row_based_on_crown_dependency_data(row, options):
            return False  # handle crown depenency options
        elif self.reject_row_based_on_northern_ireland_data(row, options):
            return False  # handle northern ireland options

        return True

    def check_options_are_valid(self, options):
        # Check our crown-dependencies option is valid
        if not options['crown-dependencies'] in ('include', 'exclude', 'only'):
            raise RuntimeError(('Invalid value for --crown-dependencies "%s" must'
                                ' be "include", "exclude", or "only".') % options['crown-dependencies'])
        # Check our northern-ireland option is valid
        if not options['northern-ireland'] in ('include', 'exclude', 'only'):
            raise RuntimeError(('Invalid value for --northern-ireland "%s" must '
                                'be "include", "exclude", or "only".') % options['northern-ireland'])
        # Check we're not trying to "only" import both
        if (options['crown-dependencies'] == 'only') and (options['northern-ireland'] == 'only'):
            raise RuntimeError(('Cannot support "only" as value for both '
                                '--northern-ireland and --crown-dependencies'))

    def location_available_for_row(self, row):
        return row[FIELD_PQI] != '9'  # PO Box etc.

    def crown_dependency_postcode(self, row):
        return row[FIELD_CODE][0:2] in ('GY', 'JE', 'IM')

    def northern_ireland_postcode(self, row):
        return row[FIELD_CODE][0:2] == 'BT'

    def reject_row_based_on_location_data(self, row, options):
        if self.location_available_for_row(row):
            return False  # don't reject rows with locations
        elif self.allow_row_with_no_location(row, options):
            return False  # don't reject rows without locations if we allow them
        else:
            return True   # no location and not allowed, reject

    def reject_row_based_on_termination_data(self, row, options):
        return row[FIELD_END_DATE] and not options['include-terminated']

    def allow_row_with_no_location(self, row, options):
        # crown dependencies have no location data in ONSPD so we allow the
        # row and defer the decision to reject the row until we examine the
        # 'crown-dependencies' option.
        return options['include-no-location'] or self.crown_dependency_postcode(row)

    def reject_row_based_on_crown_dependency_data(self, row, options):
        if self.crown_dependency_postcode(row):
            return options['crown-dependencies'] == 'exclude'  # reject if we should exclude these codes
        elif options['crown-dependencies'] == 'only':
            return True  # if we're only importing these codes, reject other codes
        else:
            return False  # otherwise keep

    def reject_row_based_on_northern_ireland_data(self, row, options):
        if self.northern_ireland_postcode(row):
            return options['northern-ireland'] == 'exclude'  # reject if we should exclude these codes
        elif options['northern-ireland'] == 'only':
            return True  # if we're only importing these codes, reject other codes
        else:
            return False  # otherwise keep
