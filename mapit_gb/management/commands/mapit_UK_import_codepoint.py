# This script is used to import Great Britain postcode information from
# Code-Point Open, released by the Ordnance Survey. Compared to the
# scripts we had in 2003, and that the data is free, I'm in heaven.
#
# The fields of a Code-Point Open CSV file before August 2011 are:
#   Postcode, Quality, 8 blanked out fields, Easting, Northing, Country,
#   NHS region, NHS health authority, County, District, Ward, blanked field
#
# The fields after August 2011, with blank fields removed and with new GSS
# codes, are: Postcode, Quality, Easting, Northing, Country, NHS region, NHS
# health authority, County, District, Ward

from mapit.management.commands.mapit_import_postal_codes import Command


class Command(Command):
    help = 'Import OS Code-Point Open postcodes'
    args = '<Code-Point CSV files>'
    often = 10000
    option_defaults = {'strip': True, 'srid': 27700}

    def pre_row(self, row, options):
        if row[1] == '90':
            return False  # Bad postcode
        # A new Code-Point only has 10 columns
        if len(row) == 10:
            options['coord-field-lon'] = 3
            options['coord-field-lat'] = 4
        else:
            options['coord-field-lon'] = 11
            options['coord-field-lat'] = 12
        return True
