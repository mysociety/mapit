# coding=UTF-8
# This script is used to import information from OSNI releases,
# which contains digital boundaries for administrative areas within
# Northern Ireland.

import sys
import csv
import os

from django.core.management.base import BaseCommand
# Not using LayerMapping as want more control, but what it does is what this does
# from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource
from django.utils import six
from django.conf import settings

from mapit.models import Area, Name, Generation, Country, Type, CodeType, NameType
from mapit.management.command_utils import save_polygons, fix_invalid_geos_geometry


class Command(BaseCommand):
    help = 'Import OSNI releases'

    def add_arguments(self, parser):
        parser.add_argument(
            '--control', action='store', dest='control',
            help='Refer to a Python module that can tell us what has changed')
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')
        parser.add_argument(
            '--lgw', action='store', dest='lgw_file',
            help='Name of OSNI shapefile that contains Ward boundary information'
        )
        parser.add_argument(
            '--wmc', action='store', dest='wmc_file',
            help=(
                'Name of OSNI shapefile that contains Westminister Parliamentary constituency boundary'
                'information (also used for Northern Ireland Assembly constituencies)'
            )
        )
        parser.add_argument(
            '--lgd', action='store', dest='lgd_file',
            help='Name of OSNI shapefile that contains Council boundary information')
        parser.add_argument(
            '--lge', action='store', dest='lge_file',
            help='Name of OSNI shapefile that contains Electoral Area boundary information')
        parser.add_argument(
            '--eur', action='store', dest='eur_file',
            help='Name of OSNI shapefile that contains European Region boundary information')

        # OSNI datasets are exported in either 29902 or 102100 projections.
        # PostGIS doesn't support 102100, but it is mathematically equivalent
        # to 3857 which it does support.  Unfortunately using that projection
        # causes failures during for point-based lookup of parents, but if we
        # use 4326 instead it works.  Apparently 102100 and 4326 are both "web
        # mercator" projections so are probably very similar (if not exactly
        # mathematically equivalent).  Interestingly opening a shapefile that is
        # in 102100 in a viewing tool such as qgis reports it as 4326 whereas a
        # 29902 reports as a custom projection that is identical in all but name
        # to 29902.  This suggests it's safe to use 4326 as a replacement for
        # 102100.  The defaults here are based on the srids of the data
        # downloaded in Dec 2015 - they may change over time.
        parser.add_argument(
            '--lgw-srid', action='store', type=int, dest='lgw_srid', default=4326,
            help='SRID of Ward boundary information shapefile (default 4326)')
        parser.add_argument(
            '--wmc-srid', action='store', type=int, dest='wmc_srid', default=4326,
            help='SRID of Westminister Parliamentery constituency boundary information shapefile (default 4326)')
        parser.add_argument(
            '--lgd-srid', action='store', type=int, dest='lgd_srid', default=4326,
            help='SRID of Council boundary information shapefile (default 4326)')
        parser.add_argument(
            '--lge-srid', action='store', type=int, dest='lge_srid', default=29902,
            help='SRID of Electoral Area boundary information shapefile (default 29902)')
        parser.add_argument(
            '--eur-srid', action='store', type=int, dest='eur_srid', default=29902,
            help='SRID of European Region boundary information shapefile (default 29902)')

    ons_code_to_shape = {}
    osni_object_id_to_shape = {}

    def handle(self, **options):
        if not options['control']:
            raise Exception("You must specify a control file")
        __import__(options['control'])
        control = sys.modules[options['control']]

        if all(options[x] is None for x in ['lgw_file', 'lgd_file', 'lge_file', 'wmc_file', 'eur_file']):
            raise Exception("You must specify at least one of lgw, wmc, lgd, lge, or eur.")

        if options['lgw_file']:
            self.process_file(options['lgw_file'], 'LGW', options['lgw_srid'], control, options)

        if options['lge_file']:
            self.process_file(options['lge_file'], 'LGE', options['lge_srid'], control, options)

        if options['lgd_file']:
            self.process_file(options['lgd_file'], 'LGD', options['lgd_srid'], control, options)

        if options['wmc_file']:
            self.process_file(options['wmc_file'], 'WMC', options['wmc_srid'], control, options)
            self.process_file(options['wmc_file'], 'NIE', options['wmc_srid'], control, options)

        if options['eur_file']:
            self.process_file(options['eur_file'], 'EUR', options['eur_srid'], control, options)

    def process_file(self, filename, area_code, srid, control, options):
        code_version = CodeType.objects.get(code=control.code_version())
        name_type = NameType.objects.get(code='N')
        code_type_osni = CodeType.objects.get(code='osni_oid')
        if not hasattr(self, area_code):
            raise Exception("Don't know how to extract features from %s files" % area_code)

        area_code_info = getattr(self, area_code)(srid)

        print(filename)
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        ds = DataSource(filename)
        layer = ds[0]

        for feat in layer:
            name, ons_code, osni_object_id = area_code_info.extract_fields(feat)
            name = self.format_name(name)
            if ons_code in self.ons_code_to_shape:
                m, poly = self.ons_code_to_shape[ons_code]
                try:
                    m_name = m.names.get(type=name_type).name
                except Name.DoesNotExist:
                    m_name = m.name  # If running without commit for dry run, so nothing being stored in db
                if name != m_name:
                    raise Exception("ONS code %s is used for %s and %s" % (ons_code, name, m_name))
                # Otherwise, combine the two shapes for one area
                poly.append(feat.geom)
                continue

            if osni_object_id in self.osni_object_id_to_shape:
                m, poly = self.osni_object_id_to_shape[osni_object_id]
                try:
                    m_name = m.names.get(type=name_type).name
                except Name.DoesNotExist:
                    m_name = m.name  # If running without commit for dry run, so nothing being stored in db
                if name != m_name:
                    raise Exception("OSNI Object ID code %s is used for %s and %s" % (osni_object_id, name, m_name))
                # Otherwise, combine the two shapes for one area
                poly.append(feat.geom)
                continue

            country = 'N'

            try:
                check = control.check(name, area_code, country, feat.geom)
                if check is True:
                    raise Area.DoesNotExist
                if isinstance(check, Area):
                    m = check
                    ons_code = m.codes.get(type=code_version).code
                elif ons_code:
                    m = Area.objects.get(codes__type=code_version, codes__code=ons_code)
                elif osni_object_id:
                    m = Area.objects.get(
                        codes__type=code_type_osni, codes__code=osni_object_id,
                        generation_high=current_generation
                    )
                    m_name = m.names.get(type=name_type).name
                    if name != m_name:
                        raise Exception(
                            "OSNI Object ID code %s is %s in DB but %s in SHP file" %
                            (osni_object_id, m_name, name)
                        )
                else:
                    raise Exception(
                        'Area "%s" (%s) has neither ONS code nor OSNI Object ID' %
                        (name, area_code)
                    )
                if int(options['verbosity']) > 1:
                    print("  Area matched, %s" % (m, ))
            except Area.DoesNotExist:
                area_type = Type.objects.get(code=area_code)
                # It's possible we already have NIE entries (without any codes) in the db
                try:
                    if area_code == 'NIE':
                        matching_name = name.title().replace('And', 'and')
                        m = Area.objects.get(name=matching_name, type=area_type, generation_high=current_generation)
                        if int(options['verbosity']) > 1:
                            print("  Area matched (via name), %s" % (m, ))
                    else:
                        raise Area.DoesNotExist("Still doesn't exist")
                except Area.DoesNotExist:
                    print("  New area: %s %s %s %s" % (area_code, ons_code, osni_object_id, name))
                    m = Area(
                        name=name,  # Not overwritten by m.names.update_or_create as no "N" use
                        type=area_type,
                        country=Country.objects.get(code=country),
                        generation_low=new_generation,
                        generation_high=new_generation,
                    )

            if m.generation_high and current_generation and m.generation_high.id < current_generation.id:
                raise Exception("Area %s found, but not in current generation %s" % (m, current_generation))
            m.generation_high = new_generation
            if options['commit']:
                m.save()

            # Make a GEOS geometry only to check for validity:
            g = feat.geom
            geos_g = g.geos
            if not geos_g.valid:
                print("  Geometry of %s %s not valid" % (ons_code, m))
                geos_g = fix_invalid_geos_geometry(geos_g)
                if geos_g is None:
                    raise Exception("The geometry for area %s was invalid and couldn't be fixed" % name)
                    g = None
                else:
                    g = geos_g.ogr

            g = area_code_info.transform_geom(g)
            poly = [g]

            if options['commit']:
                m.names.update_or_create(type=name_type, defaults={'name': name})
            if ons_code:
                self.ons_code_to_shape[ons_code] = (m, poly)
                if options['commit']:
                    m.codes.update_or_create(type=code_version, defaults={'code': ons_code})
            if osni_object_id:
                self.osni_object_id_to_shape[osni_object_id] = (m, poly)
                if options['commit']:
                    m.codes.update_or_create(type=code_type_osni, defaults={'code': osni_object_id})

        if options['commit']:
            save_polygons(self.osni_object_id_to_shape)
            save_polygons(self.ons_code_to_shape)

    class AreaCodeShapefileInterpreter(object):
        def __init__(self, srid):
            self.srid = srid

        # Transform all shapefile geometry to the MAPIT_AREA_SRID if it's
        # not already in that projection - otherwise the data is assumed to
        # be in that projection when saved, regardless of the srid specified
        # on the geometry object
        def transform_geom(self, geom):
            geom.srid = self.srid
            if not(self.srid == settings.MAPIT_AREA_SRID):
                geom.transform(settings.MAPIT_AREA_SRID)
            return geom

    class WMC(AreaCodeShapefileInterpreter):
        def extract_fields(self, feature):
            name = feature['PC_NAME'].value
            ons_code = feature['PC_ID'].value
            object_id = 'WMC-%s' % str(feature['OBJECTID'].value)
            return (name, ons_code, object_id)

    class NIE(AreaCodeShapefileInterpreter):
        # We don't have GSS codes for NIE areas, because we generate them from
        # the WMC data and can't have duplicates
        def extract_fields(self, feature):
            name = feature['PC_NAME'].value
            object_id = 'NIE-%s' % str(feature['OBJECTID'].value)
            return (name, None, object_id)

    class LGW(AreaCodeShapefileInterpreter):
        def extract_fields(self, feature):
            name = feature['WARDNAME'].value
            ons_code = feature['WardCode'].value
            object_id = 'LGW-%s' % str(feature['OBJECTID'].value)
            return (name, ons_code, object_id)

    class LGD(AreaCodeShapefileInterpreter):
        def extract_fields(self, feature):
            name = feature['LGDNAME'].value
            ons_code = feature['LGDCode'].value
            object_id = 'LGD-%s' % str(feature['OBJECTID'].value)
            return (name, ons_code, object_id)

    class LGE(AreaCodeShapefileInterpreter):
        def __init__(self, srid):
            super(self.__class__, self).__init__(srid)
            self.lge_ons_codes = {}
            self._populate_osni_missing_ons_codes()

        def _populate_osni_missing_ons_codes(self):
            ni_areas = csv.reader(open(os.path.dirname(__file__) + '/../../data/ni-electoral-areas-2015.csv'))
            next(ni_areas)  # comment line
            next(ni_areas)  # header row
            for _lgd_name, _lgd_gss_code, lge_name, lge_gss_code, _lgw_name, _lgw_gss_code in ni_areas:
                if not lge_name:
                    next
                else:
                    if lge_name not in self.lge_ons_codes:
                        self.lge_ons_codes[lge_name] = lge_gss_code

        def extract_fields(self, feature):
            name = feature['FinalR_DEA'].value
            if name in self.lge_ons_codes:
                ons_code = self.lge_ons_codes[name]
            else:
                ons_code = None
            object_id = 'LGE-%s' % str(feature['OBJECTID'].value)
            return (name, ons_code, object_id)

    class EUR(AreaCodeShapefileInterpreter):
        def extract_fields(self, feature):
            object_id = 'EUR-%s' % str(feature['OBJECTID'].value)
            return ('Northern Ireland', 'N07000001', object_id)

    def format_name(self, name):
        if not isinstance(name, six.text_type):
            name = name.decode('iso-8859-1')
        return name
