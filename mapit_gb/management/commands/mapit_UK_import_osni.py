# coding=UTF-8
# This script is used to import information from OSNI releases,
# which contains digital boundaries for administrative areas within
# Northern Ireland.

import sys
import csv
import os
from optparse import make_option

from django.core.management.base import NoArgsCommand
# Not using LayerMapping as want more control, but what it does is what this does
# from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource
from django.utils import six

from mapit.models import Area, Name, Generation, Country, Type, CodeType, NameType
from mapit.management.command_utils import save_polygons, fix_invalid_geos_geometry


class Command(NoArgsCommand):
    help = 'Import OSNI releases'
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--control', action='store', dest='control',
            help='Refer to a Python module that can tell us what has changed'),
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
        make_option(
            '--lgw', action='store', dest='lgw_file',
            help='Name of OSNI shapefile that contains Ward boundary information'
        ),
        make_option(
            '--wmc', action='store', dest='wmc_file',
            help=(
                'Name of OSNI shapefile that contains Westminister Parliamentary constituency boundary'
                'information (also used for Northern Ireland Assembly constituencies)'
            )
        ),
        make_option(
            '--lgd', action='store', dest='lgd_file',
            help='Name of OSNI shapefile that contains Council boundary information'),
    )

    ons_code_to_shape = {}
    osni_object_id_to_shape = {}

    def handle_noargs(self, **options):
        if not options['control']:
            raise Exception("You must specify a control file")
        __import__(options['control'])
        control = sys.modules[options['control']]

        if all(options[x] is None for x in ['lgw_file', 'lgd_file', 'wmc_file']):
            raise Exception("You must specify at least one of lgw, wmc, or lgd.")

        if options['lgw_file']:
            self.process_file(options['lgw_file'], 'LGW', control, options)

        if options['lgd_file']:
            self.process_file(options['lgd_file'], 'LGD', control, options)

        if options['wmc_file']:
            self.process_file(options['wmc_file'], 'WMC', control, options)
            self.process_file(options['wmc_file'], 'NIE', control, options)

    def process_file(self, filename, area_code, control, options):
        code_version = CodeType.objects.get(code=control.code_version())
        name_type = NameType.objects.get(code='N')
        code_type_osni = CodeType.objects.get(code='osni_oid')

        print(filename)
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        ds = DataSource(filename)
        layer = ds[0]

        if area_code not in self.area_code_to_feature_field:
            raise Exception("Don't know how to extract features from %s files" % area_code)

        for feat in layer:
            name, ons_code, osni_object_id = self.extract_fields_from_feature(feat, area_code)
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
                print("  New area: %s %s %s %s" % (area_code, ons_code, osni_object_id, name))
                m = Area(
                    name=name,  # If committing, this will be overwritten by the m.names.update_or_create
                    type=Type.objects.get(code=area_code),
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

    def extract_fields_from_feature(self, feature, area_code):
        name = self.extract_field_from_feature(feature, area_code, 'name')
        name = self.format_name(name)

        ons_code = self.extract_field_from_feature(feature, area_code, 'ons_code')

        osni_object_id = self.extract_field_from_feature(feature, area_code, 'osni_object_id')
        osni_object_id = "%s-%s" % (area_code, str(osni_object_id))

        return (name, ons_code, osni_object_id)

    def extract_field_from_feature(self, feature, area_code, field):
        if field in self.area_code_to_feature_field[area_code]:
            self.area_code_to_feature_field[area_code][field].value
        else:
            return None

    area_code_to_feature_field = {
        'WMC': {'name': 'PC_NAME', 'ons_code': 'PC_ID', 'osni_object_id': 'OBJECTID'},
        # We don't have GSS codes for NIE areas, because we generate them from
        # the WMC data and can't have duplicates
        'NIE': {'name': 'PC_NAME', 'osni_object_id': 'OBJECTID'},
        'LGD': {'name': 'LGDNAME', 'ons_code': 'LGDCode', 'osni_object_id': 'OBJECTID'},
        'LGW': {'name': 'WARDNAME', 'ons_code': 'WardCode', 'osni_object_id': 'OBJECTID'},
    }

    def format_name(self, name):
        if not isinstance(name, six.text_type):
            name = name.decode('iso-8859-1')
        return name
