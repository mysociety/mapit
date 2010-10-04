# This script is used to import boundary polygons and other information
# from the ONS's CD-ROM of Super Output Areas for England and Wales.  
# Information about the CD-ROM here: http://bit.ly/63bX97

# Run as: ./manage.py import_soa shapefile.shp

import re
import sys
from optparse import make_option
from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import *
from mapit.areas.models import Area, Generation

class Command(LabelCommand):
    help = 'Creates Super Output Area boundaries from ONS shapefiles'
    args = '<ONS SOA shapefile>'

    lsoa_code_to_shape = {}

    def handle_label(self, filename, **options):
        print filename
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        short_filename = filename.split("/")[-1]
        filename_prefix = short_filename[:4]
        filename_suffix = short_filename.split(".")[0][-3:]

        # check shapefile type - we handle both LSOA and MSOA
        if filename_prefix=="LSOA":
            feat_name = 'LSOA04NM'
            feat_code = 'LSOA04CD'
            if filename_suffix=='BGC':
                area_type = 'OLG'
            else: 
                area_type = 'OLF'
        elif filename_prefix=="MSOA":
            feat_name = 'MSOA04NM'
            feat_code = 'MSOA04CD'
            if filename_suffix=='BGC':
                area_type = 'OMG'
            else: 
                area_type = 'OMF'
        else:
            raise Exception, "Sorry, this script only handles LSOA/MSOA shapefiles!"            
    
        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            # retrieve name and code, and set country
            name = feat[feat_name].value
            lsoa_code = feat[feat_code].value 
            country = lsoa_code[0]
            # check if the LOA already exists in db, create it if not
            try:
                m = Area.objects.get(codes__type=area_type, codes__code=lsoa_code)
            except Area.DoesNotExist:
                m = Area(
                    type = area_type,
                    country = country,
                    generation_low = new_generation,
                    generation_high = new_generation,
                )
            # check the generation
            if m.generation_high and m.generation_high.id < current_generation:
                raise Exception, "Area %s found, but not in current generation %s" % (m, current_generation)
            m.generation_high = new_generation
            m.save()
            poly = [ feat.geom ]
            # TODO: check, is this type correct? 
            m.names.update_or_create({ 'type': 'S' }, { 'name': name })
            self.lsoa_code_to_shape[lsoa_code] = (m, poly)
            m.codes.update_or_create({ 'type': 'ons' }, { 'code': lsoa_code })

        # save all the polygons once done
        self.save_polygons(self.lsoa_code_to_shape)

    def save_polygons(self, lookup): # copied from import_boundary_line
        for shape in lookup.values():
            m, poly = shape
            if not poly:
                continue
            sys.stdout.write(".")
            sys.stdout.flush()
            #g = OGRGeometry(OGRGeomType('MultiPolygon'))
            m.polygons.all().delete()
            for p in poly:
                print p.geom_name
                if p.geom_name == 'POLYGON':
                    shapes = [ p ]
                else:
                    shapes = p
                for g in shapes:
                    m.polygons.create(polygon=g.wkt)
            #m.polygon = g.wkt
            #m.save()
            poly[:] = [] # Clear the polygon's list, so that if it has both an ons_code and unit_id, it's not processed twice
        print ""
