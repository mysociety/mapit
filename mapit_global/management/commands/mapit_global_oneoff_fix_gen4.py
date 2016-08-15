# This script is used one-off to fix the incorrectly slightly-rounded
# boundaries of the import that was Generation 4 of global MapIt.

from glob import glob
import os
import re

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from django.utils.encoding import smart_str, smart_text
import shapely

from mapit.models import Generation, Code, CodeType
from mapit.management.command_utils import save_polygons
from mapit.management.command_utils import fix_invalid_geos_multipolygon


class Command(LabelCommand):
    help = 'Update OSM boundary data from KML files'
    args = '<KML-DIRECTORY>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle_label(self, directory_name, **options):
        current_generation = Generation.objects.current()

        if not os.path.isdir(directory_name):
            raise Exception("'%s' is not a directory" % (directory_name,))

        os.chdir(directory_name)

        mapit_type_glob = smart_text("[A-Z0-9][A-Z0-9][A-Z0-9]")

        if not glob(mapit_type_glob):
            raise Exception(
                "'%s' did not contain any directories that look like MapIt types (e.g. O11, OWA, etc.)" % (
                    directory_name,))

        def verbose(s):
            if int(options['verbosity']) > 1:
                print(smart_str(s))

        verbose("Loading any admin boundaries from " + directory_name)
        for type_directory in sorted(glob(mapit_type_glob)):

            verbose("Loading type " + type_directory)

            if not os.path.exists(type_directory):
                verbose("Skipping the non-existent " + type_directory)
                continue

            verbose("Loading all KML in " + type_directory)

            files = sorted(os.listdir(type_directory))
            total_files = len(files)

            for i, e in enumerate(files):
                progress = "[%d%% complete] " % ((i * 100) / total_files,)

                if not e.endswith('.kml'):
                    verbose("Ignoring non-KML file: " + e)
                    continue

                m = re.search(r'^(way|relation)-(\d+)-', e)
                if not m:
                    raise Exception("Couldn't extract OSM element type and ID from: " + e)

                osm_type, osm_id = m.groups()
                kml_filename = os.path.join(type_directory, e)
                verbose(progress + "Loading " + os.path.realpath(kml_filename))

                if osm_type == 'relation':
                    code_type_osm = CodeType.objects.get(code='osm_rel')
                elif osm_type == 'way':
                    code_type_osm = CodeType.objects.get(code='osm_way')
                else:
                    raise Exception("Unknown OSM element type: " + osm_type)

                ds = DataSource(kml_filename)
                layer = ds[0]
                if len(layer) != 1:
                    raise Exception("We only expect one feature in each layer")

                feat = layer[1]

                g = feat.geom.transform(4326, clone=True)

                if g.geom_count == 0:
                    verbose('    Ignoring that file - it contained no polygons')
                    continue

                polygons_too_small = 0
                for polygon in g:
                    if polygon.num_points < 4:
                        polygons_too_small += 1
                if polygons_too_small:
                    message = "%d out of %d polygon(s) were too small" % (polygons_too_small, g.geom_count)
                    verbose('    Skipping, since ' + message)
                    continue

                g_geos = g.geos
                if not g_geos.valid:
                    verbose("    Invalid KML:" + kml_filename)
                    fixed_multipolygon = fix_invalid_geos_multipolygon(g_geos)
                    if len(fixed_multipolygon) == 0:
                        verbose("    Invalid polygons couldn't be fixed")
                        continue
                    g = fixed_multipolygon.ogr

                osm_code = Code.objects.get(
                    type=code_type_osm,
                    code=osm_id,
                    area__generation_high__lte=current_generation,
                    area__generation_high__gte=current_generation)

                m = osm_code.area

                previous_geos_geometry = m.polygons.collect()
                previous_geos_geometry = shapely.wkb.loads(str(previous_geos_geometry.simplify(tolerance=0).ewkb))
                new_geos_geometry = shapely.wkb.loads(str(g.geos.simplify(tolerance=0).ewkb))
                if previous_geos_geometry.almost_equals(new_geos_geometry, decimal=7):
                    verbose('    Boundary unchanged')
                else:
                    verbose('    In the current generation, the boundary was different')
                    poly = [g]
                    if options['commit']:
                        save_polygons({'dummy': (m, poly)})
