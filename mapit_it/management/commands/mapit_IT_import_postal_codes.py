# This is a generic script for importing postal codes in some format from a CSV
# file. The CSV file should have the following columns:
#   Postal code, Latitude, Longitude
# By default in those positions, though you can specify other column numbers on
# the command line

from optparse import make_option
from django.contrib.gis.geos import Point
from django.core.management.base import LabelCommand
import requests
import time
from mapit.management.commands.mapit_import_postal_codes import Command as pcCommand


class Command(pcCommand):


    help = 'Import Postal codes from a CSV file or files'
    args = '<CSV files>'
    count = {'total': 0, 'updated': 0, 'unchanged': 0, 'created': 0}
    often = 10
    nominatim_url = "http://nominatim.openstreetmap.org/"

    option_defaults = {}
    option_list = LabelCommand.option_list + (
        make_option(
            '--code-field',
            action='store',
            dest='code-field',
            default=1,
            help='The column of the CSV containing the postal code (default 1, first)'
        ),
        make_option(
            '--coord-field-lat',
            action='store',
            dest='coord-field-lat',
            default=None,
            help='The column of the CSV containing the lat/y co-ordinate (default 2)'
        ),
        make_option(
            '--coord-field-lon',
            action='store',
            dest='coord-field-lon',
            default=None,
            help='The column of the CSV containing the lon/x co-ordinate (default --coord-field-lat + 1)'
        ),
        make_option(
            '--header-row',
            action='store_true',
            dest='header-row',
            default=False,
            help='Set if the CSV file has a header row'
        ),
        make_option(
            '--no-location',
            action="store_false",
            dest='location',
            default=True,
            help='Set if the postal codes have no associated location (still useful for existence checks)'
        ),
        make_option(
            '--srid',
            action="store",
            dest='srid',
            default=4326,
            help='The SRID of the projection for the data given (default 4326 WGS-84)'
        ),
        make_option(
            '--strip',
            action="store_true",
            dest='strip',
            default=False,
            help='Whether to strip all spaces from the postal code before import'
        ),
        make_option(
            '--tabs',
            action="store_true",
            dest='tabs',
            default=False,
            help='If the CSV file actually uses tab as its separator'
        ),
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
