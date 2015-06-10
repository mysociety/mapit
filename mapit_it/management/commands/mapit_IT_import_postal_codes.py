# This is a generic script for importing postal codes in some format from a CSV
# file. The CSV file should have the following columns:
#   Postal code, Latitude, Longitude
# By default in those positions, though you can specify other column numbers on
# the command line

from optparse import make_option
from django.contrib.gis.geos import Point
import requests
import time
from mapit.management.commands.mapit_import_postal_codes import Command as pcCommand


class Command(pcCommand):
    help = 'Import Postal codes from a CSV file or files'
    args = '<CSV files>'
    count = {'total': 0, 'updated': 0, 'unchanged': 0, 'created': 0}
    often = 10
    nominatim_url = "http://nominatim.openstreetmap.org/"

    def create_parser(self, prog_name, subcommand):
        parser = super(Command, self).create_parser(prog_name, subcommand)
        parser.set_defaults(**{'coord-field-lat': None, 'coord-field-lon': None})
        return parser

    option_list = pcCommand.option_list + (
        make_option(
            '--nominatim-sleep-time',
            action="store",
            dest='nominatim-sleep-time',
            default="0.25",
            help='The n. of seconds to wait before two subsequent requests'
        ),
    )

    def handle_row(self, row, options):
        if not options['location']:
            return self.do_postcode()

        if not options['coord-field-lat']:
            # request lat and lon to nominatim
            req = "{0}search?format=json&country=it&postalcode={1}".format(
                self.nominatim_url, self.code
            )
            try:
                print u"Requesting {0}".format(req)
                r = requests.get(req).json()[0]
                lat = float(r['lat'])
                lon = float(r['lon'])
            except Exception as e:
                print u"Exception: {0}".format(e)
                print u"Skipping."
                return
            # sleep before successive request
            time.sleep(float(options['nominatim-sleep-time']))
        else:
            if not options['coord-field-lon']:
                options['coord-field-lon'] = int(options['coord-field-lat']) + 1
            lat = float(row[int(options['coord-field-lat']) - 1])
            lon = float(row[int(options['coord-field-lon']) - 1])
        srid = int(options['srid'])
        location = Point(lon, lat, srid=srid)
        return self.do_postcode(location, srid)
