# This script is used to import Crown Dependency postcode information from the
# National Statistics Postcode Database.
# http://www.ons.gov.uk/about-statistics/geography/products/geog-products-postcode/nspd/

from mapit.management.commands.mapit_import_postal_codes import Command
from optparse import make_option

class Command(Command):
    help = 'Imports Crown Dependency postcodes from the NSPD'
    args = '<NSPD CSV file>'
    option_defaults = {'strip': True, 'location': False}
    option_list = Command.option_list + (
        make_option(
            '--allow-terminated-postcodes',
            action='store_true',
            dest='include-terminated',
            default=False,
            help='Set if you want to import terminated postcodes'
        ),
    )

    def pre_row(self, row, options):
        if row[4] and not options['include-terminated']:
            return False  # Terminated postcode
        if self.code[0:2] not in ('GY', 'JE', 'IM'):
            return False  # Only importing Crown dependencies from NSPD
        return True
