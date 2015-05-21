# This script is used to import NHS England CCG area boundaries into MapIt.
# These boundaries are available as open data from:
#
# http://www.england.nhs.uk/wp-content/uploads/2013/03/ccg-kml-format.zip
#
# Unfortunately, they aren't very usefully formatted - the names
# are embedded in an (incomplete) HTML table in the description field. e.g:
#
# <description><![CDATA[<br><br><br>
#    <table border="1" padding="0">
#    <tr><td>CCGcode</td><td>00C</td></tr>
#    <tr><td>CCGname</td><td>NHS Darlington CCG</td></tr>
#        ]]></description>
#
# This script deals with this problem, importing the names into MapIt cleanly.

from lxml import etree
from optparse import make_option

from django.core.management import call_command
from django.core.management.base import LabelCommand, CommandError

from django.contrib.gis.gdal import DataSource

from mapit.models import Country, Area, Name


class Command(LabelCommand):

    help = 'Import NHS England CCG boundaries from .kml file'
    args = '<KML file>'
    option_list = LabelCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'
        ),
        make_option(
            '--generation_id',
            action="store",
            dest='generation_id',
            help='Which generation ID should be used',
        ),
        make_option(
            '--area_type_code',
            action="store",
            dest='area_type_code',
            help='Which area type should be used (specify using code)',
        ),
        make_option(
            '--name_type_code',
            action="store",
            dest='name_type_code',
            help='Which name type should be used (specify using code)',
        ),
        make_option(
            '--code_type',
            action="store",
            dest='code_type',
            help='Which code type should be used (specify using its code)',
        ),
        make_option(
            '--use_code_as_id',
            action="store_true",
            dest='use_code_as_id',
            help="Set to use the code from code_field as the MapIt ID"
        ),
        make_option(
            '--preserve',
            action="store_true",
            dest='preserve',
            help="Create a new area if the name's the same but polygons differ"
        ),
        make_option(
            '--new',
            action="store_true",
            dest='new',
            help="Don't look for existing areas at all, just import everything as new areas"
        ),
        make_option(
            '--encoding',
            action="store",
            dest='encoding',
            help="The encoding of names in this dataset"
        ),
        make_option(
            '--fix_invalid_polygons',
            action="store_true",
            dest='fix_invalid_polygons',
            help="Try to fix any invalid polygons and multipolygons found"
        ),
    )


    # ensure all required_params are in options
    def check_params(self, required_params, options):
        missing_options = []
        for k in required_params:
            if options[k]:
                continue
            else:
                missing_options.append(k)
        if missing_options:
            message_start = "Missing arguments " if len(missing_options) > 1 else "Missing argument "
            message = message_start + " ".join('--{0}'.format(k) for k in missing_options)
            raise CommandError(message)


    def extract_name_from_description(self, description):

        table = etree.XML(description)
        rows = iter(table)
        rowcount = 0
        for row in rows:
            cols = iter(row)
            colcount = 0
            for col in cols:
                if ((rowcount == 1) and (colcount == 1)):
                    name = col.text
                    break
                colcount += 1
            rowcount += 1

        return name


    def update_main_area_name(self, code_type, ccg_code, ccg_name):
        try:
            area = Area.objects.get(codes__type__code=code_type, codes__code=ccg_code)
            area.name = ccg_name
            area.save()

            self.stdout.write("Updated area name.")
            return area.id
        except:
            self.stdout.write("Failed to update area name for area code '%s'" % ccg_code)


    def update_specific_type_name(self, area_id, name_type_code, ccg_code, ccg_name):
        try:
            name = Name.objects.get(area=area_id, type__code=name_type_code)
            name.name = ccg_name
            name.save()

            self.stdout.write("Updated %s name." % name_type_code)
        except:
            self.stdout.write("Failed to update %s name for area code '%s'" % (name_type_code, ccg_code))



    def handle_label(self, filename, **options):

        # required params
        self.check_params(['generation_id', 'area_type_code', 'name_type_code', 'code_type'], options)

        # check England exists
        try:
            Country.objects.get(code='E')
        except Country.DoesNotExist:
            raise CommandError("England doesn't exist yet; load the UK fixture first.")


        self.stdout.write("Importing NHS CCG areas from %s" % filename)

        command_kwargs = options
        # set up the hard-coded params
        command_kwargs['override_name'] = None
        command_kwargs['override_code'] = None
        command_kwargs['country_code']  = 'E'
        command_kwargs['code_field']    = 'name'
        command_kwargs['name_field']    = 'name'

        call_command(
            'mapit_import',
            filename,
            **command_kwargs
        )


        # after importing the boundaries, extract area names

        self.stdout.write('Attaching CCG names...')

        ds = DataSource(filename)
        layer = ds[0]
        for feature in layer:
            ccg_code = feature['name'].value
            description = feature['description'].value

            # tidy up description so it will parse nicely
            description = description[12:].strip().replace('&', '&amp;') + '</table>'

            ccg_name = self.extract_name_from_description(description)

            self.stdout.write("Found name '%s' for area code '%s'" % (ccg_name, ccg_code))


            # if --commit param set, update DB with the name we've found.
            if options['commit']:

                area_id = self.update_main_area_name(options['code_type'], ccg_code, ccg_name)
                if area_id:
                    self.update_specific_type_name(area_id, options['name_type_code'], ccg_code, ccg_name)
