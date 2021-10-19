# This script is used to import NCP information from OS Boundary-Line.

import csv
import re

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource

from mapit.models import Area, Generation, Country, Type, CodeType, NameType
from mapit.management.command_utils import save_polygons


class Command(LabelCommand):
    help = 'Import OS Boundary-Line NCP areas'
    label = '<parish shapefile>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--mapping', help='Mapping from NCP code to name')
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    name_to_shape = {}

    def handle_label(self, filename, **options):
        code_version = CodeType.objects.get(code='gss')
        name_type = NameType.objects.get(code='O')
        type = Type.objects.get(code='NCP')
        country = Country.objects.get(code='E')

        self.current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        mapping = self.construct_ncp_code_mapping(options["mapping"])

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            # Only care about Non Parished Areas
            area_code = feat['AREA_CODE'].value
            if area_code != 'NCP':
                continue

            # Find which council this area is in
            council_area = self.area_in_england(feat)
            if not council_area:
                continue

            name = self.construct_ncp_name(council_area)

            if name in self.name_to_shape:
                # Already had a polygon in this place already
                m, poly = self.name_to_shape[name]
                poly.append(feat.geom)
                continue

            # We pop because we should only get here once per name, and can
            # then check we've got everything at the end
            ncp_code = mapping.pop(name)

            try:
                m = Area.objects.get(codes__type=code_version, codes__code=ncp_code)
                if int(options['verbosity']) > 1:
                    print("  Area matched, %s" % (m, ))
            except Area.DoesNotExist:
                print("  New area: %s %s" % (ncp_code, name))
                m = Area(
                    name=name, type=type, country=country,
                    generation_low=new_generation, generation_high=new_generation)

            if m.generation_high and self.current_generation and m.generation_high.id < self.current_generation.id:
                raise Exception("Area %s found, but not in current generation %s" % (m, self.current_generation))
            m.generation_high = new_generation
            if options['commit']:
                m.save()

            poly = [feat.geom]
            if options['commit']:
                m.names.update_or_create(type=name_type, defaults={'name': name})
                m.codes.update_or_create(type=code_version, defaults={'code': ncp_code})
            self.name_to_shape[name] = (m, poly)

        if options['commit']:
            save_polygons(self.name_to_shape)

        if mapping:
            raise Exception("Unfound mappings: %s" % mapping)

    def construct_ncp_code_mapping(self, filename):
        # Lundy is not the same list as everything else, presumably for "historical reasons"
        mapping = {
            'Torridge, unparished area': 'E04003303'
        }
        for line in csv.DictReader(open(filename)):
            name = line["NCP21NM"]
            code = line["NCP21CD"]
            if name in mapping:
                raise Exception("Already got %s" % name)
            mapping[name] = code
        return mapping

    def area_in_england(self, feat):
        g = feat.geom
        point = g.geos.point_on_surface
        if point.y > 656300:
            # Definitely Scotland
            return False

        area = Area.objects.get(
            type__code__in=['UTA', 'DIS', 'MTD', 'LBO'],
            polygons__polygon__contains=point,
            generation_high_id__gte=self.current_generation)
        if area.country.code == 'S':
            return False

        return area

    def construct_ncp_name(self, area):
        name = re.sub('( (City|Borough|District))? Council$', '', area.name)
        # Some manual overrides to match ONS file
        if name == 'Durham County':
            name = 'County Durham'
        if name == 'St Helens':
            name = 'St. Helens'
        if name == 'St Albans City and':
            name = 'St Albans'  # And yet no dot here!
        if name == 'Hull':
            name = 'Kingston upon Hull, City of'
        if name == 'Bristol':
            name = 'Bristol, City of'
        if name == 'City of York':
            name = 'York'
        if name == 'Newcastle':
            name = 'Newcastle upon Tyne'
        if name == 'City of London Corporation':
            name = 'City of London'
        name = '%s, unparished area' % name
        return name
