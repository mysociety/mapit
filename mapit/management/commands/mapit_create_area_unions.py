# create_area_unions.py:
# This script is used to create regions which are combinations of existing
# areas into MapIt. It can do so either by using the many-many relationship
# between Areas and Geometries, or by using unionagg() to actually create new,
# larger Areas.

import csv
import re
import sys
from optparse import make_option
from django.core.management.base import LabelCommand
from mapit.models import Area, Geometry, Generation, Type, Country
from mapit.management.command_utils import save_polygons

class Command(LabelCommand):
    help = 'Create areas from existing areas'
    args = '<CSV file listing IDs that make up new areas>'
    option_list = LabelCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'
        ),
        make_option(
            '--area_type_code',
            action="store",
            dest='area_type_code',
            help='Which area type should be used (specify using code)',
        ),
        make_option(
            '--header-row',
            action = 'store_true',
            dest = 'header-row',
            default = False,
            help = 'Set if the CSV file has a header row'
        ),
        make_option(
            '--region-name',
            action = 'store_true',
            dest = 'region-name',
            default = False,
            help = 'Set if the first column of the CSV file is the union name'
        ),
        make_option(
            '--region-id',
            action = 'store_true',
            dest = 'region-id',
            default = False,
            help = 'Set if the first column of the CSV file is the union ID'
        ),
        make_option(
            '--country_code',
            action="store",
            dest='country_code',
            default = None,
            help = 'Set if you want to specify country of the regions'
        ),
        make_option(
            '--unionagg',
            action = 'store_true',
            dest = 'unionagg',
            default = False,
            help = 'Set if you wish to actually create new geometries, rather than use existing ones'
        ),
    )

    def find_area(self, name):
        m = re.match('[0-9]+', name)
        if m:
            try:
                return Area.objects.get(id=int(m.group()))
            except Area.DoesNotExist:
                pass
        try:
            return Area.objects.get(name__iexact=name,
                generation_low__lte=self.current_generation,
                generation_high__gte=self.new_generation
            )
        except Area.MultipleObjectsReturned:
            raise Exception, "More than one Area named %s, use area ID as well" % name
        except Area.DoesNotExist:
            raise Exception, "Area with name %s was not found!" % name

    def handle_label(self, filename, **options):
        self.current_generation = Generation.objects.current()
        self.new_generation = Generation.objects.new()
        if not self.new_generation:
            raise Exception, "No new generation to be used for import!"

        area_type_code = options['area_type_code']
        if len(area_type_code)>3:
            print "Area type code must be 3 letters or fewer, sorry"
            sys.exit(1)
        try:
            self.area_type = Type.objects.get(code=area_type_code)
        except:
            type_desc = raw_input('Please give a description for area type code %s: ' % area_type_code)
            self.area_type = Type(code=area_type_code, description=type_desc)
            if options['commit']:
                self.area_type.save()

        country_code = options['country_code']
        if country_code:
            try:
                self.country = Country.objects.get(code=country_code)
            except:
                country_name = raw_input('Please give the name for country code %s: ' % country_code)
                self.country = Country(code=country_code, name=country_name)
                if options['commit']: self.country.save()

        print 'Loading file %s' % filename
        reader = csv.reader(open(filename))
        if options['header-row']: next(reader)
        for row in reader:
            self.handle_row(row, options)

    def handle_row(self, row, options):
        region_id = None
        region_name = None
        if options['region-name']:
            region_name = row.pop(0)
        if options['region-id']:
            region_id = row.pop(0)

        areas = []
        for name in row:
            areas.append( self.find_area(name) )

        if region_name is None:
            region_name = ' / '.join( [ area.name for area in areas ] )

        geometry = Geometry.objects.filter(areas__in=areas)
        if options['unionagg']:
            geometry = geometry.unionagg()
            geometry = [ geometry.ogr ]

        try:
            if region_id:
                area = Area.objects.get(id=int(region_id), type=self.area_type)
            else:
                area = Area.objects.get(name=region_name, type=self.area_type)
        except Area.DoesNotExist:
            area = Area(
                name            = region_name,
                type            = self.area_type,
                generation_low  = self.new_generation,
                generation_high = self.new_generation,
            )
            if region_id: area.id = int(region_id)
            if self.country: area.country = self.country

        # check that we are not about to skip a generation
        if area.generation_high and self.current_generation and area.generation_high.id < self.current_generation.id:
            raise Exception, "Area %s found, but not in current generation %s" % (area, self.current_generation)
        area.generation_high = self.new_generation

        if options['commit']:
            area.save()
            if options['unionagg']:
                save_polygons({ area.id : (area, geometry) })
            else:
                area.polygons.clear()
                for polygon in geometry:
                    area.polygons.add(polygon)

