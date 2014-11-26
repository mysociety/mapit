# This script is used to import Norwegian postcode information from
# http://www.erikbolstad.no/geo/noreg/postnummer/, released by the
# Erik Bolstad:
# http://www.erikbolstad.no/postnummer-koordinatar/txt/postnummer.csv
# You can just use the generic postal code importer for this file,
# using the arguments: --coord-field-lat 10 --header-row --tabs

from mapit.management.commands.mapit_import_postal_codes import Command


class Command(Command):
    help = 'Import Norwegian postcodes from the Erik Bolstad data set'
    args = '<CSV file>'
    option_defaults = {'coord-field-lat': 10, 'header-row': True, 'tabs': True}
