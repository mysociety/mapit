# This script is used to import postcodes from the ONS Postcode Directory:
# https://www.ons.gov.uk/methodology/geography/geographicalproducts/postcodeproducts

from mapit.management.commands.mapit_import_postal_codes import Command


class Command(Command):
    help = ('Imports UK postcodes from the ONSPD.\n\nBy default imports only '
            'live GB postcodes with a lat/lng, options are available to also '
            'import terminated, NI, or Crown Dependency postcodes and those '
            'without locations.')
    label = '<ONSPD CSV file>'
    option_defaults = {'header-row': True, 'strip': True, 'srid': 27700, 'coord-field-lon': 12, 'coord-field-lat': 13}

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
            help=('How to handle crown dependency postocdes.  Set to "include" '
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
        parser.add_argument(
            '--gb-srid',
            action='store',
            dest='gb-srid',
            default=27700,
            help=('SRID for GB & Crown Dependency postcodes. Overrides --srid '
                  'value. (Default: 27700).')
        )
        parser.add_argument(
            '--ni-srid',
            action='store',
            dest='ni-srid',
            default=29902,
            help=('SRID for NI postcodes. Overrides --srid value for. (Default:'
                  ' 29902).')
        )

    def handle_label(self, file, **options):
        self.check_options_are_valid(options)
        self.process(file, options)

    def pre_row(self, row, options):
        if self.reject_row_based_on_termination_data(row, options):
            return False  # Terminated postcode
        elif self.reject_row_based_on_location_data(row, options):
            return False  # go no further unless we want codes with no location
        elif self.reject_row_based_on_crown_dependency_data(row, options):
            return False  # handle crown depenency options
        elif self.reject_row_based_on_northern_ireland_data(row, options):
            return False  # handle northern ireland options

        if self.northern_ireland_postcode():
            options['srid'] = options['ni-srid']
        else:
            options['srid'] = options['gb-srid']

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
        return row[13] != '9'  # PO Box etc.

    def crown_dependency_postcode(self):
        return self.code[0:2] in ('GY', 'JE', 'IM')

    def northern_ireland_postcode(self):
        return self.code[0:2] == 'BT'

    def reject_row_based_on_location_data(self, row, options):
        if self.location_available_for_row(row):
            return False  # don't reject rows with locations
        elif self.allow_row_with_no_location(row, options):
            return False  # don't reject rows without locations if we allow them
        else:
            return True   # no location and not allowed, reject

    def reject_row_based_on_termination_data(self, row, options):
        return row[4] and not options['include-terminated']

    def allow_row_with_no_location(self, row, options):
        # crown dependencies have no location data in ONSPD so we allow the
        # row and defer the decision to reject the row until we examine the
        # 'crown-dependencies' option.
        return options['include-no-location'] or self.crown_dependency_postcode()

    def reject_row_based_on_crown_dependency_data(self, row, options):
        if self.crown_dependency_postcode():
            return options['crown-dependencies'] == 'exclude'  # reject if we should exclude these codes
        elif options['crown-dependencies'] == 'only':
            return True  # if we're only importing these codes, reject other codes
        else:
            return False  # otherwise keep

    def reject_row_based_on_northern_ireland_data(self, row, options):
        if self.northern_ireland_postcode():
            return options['northern-ireland'] == 'exclude'  # reject if we should exclude these codes
        elif options['northern-ireland'] == 'only':
            return True  # if we're only importing these codes, reject other codes
        else:
            return False  # otherwise keep
