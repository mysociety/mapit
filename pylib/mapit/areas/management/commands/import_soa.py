# This script is used to import boundary polygons and other information
# from the ONS's CD-ROM of Super Output Areas for England and Wales.  
# Information about the CD-ROM here: http://bit.ly/63bX97

# Run as: ./manage.py import_soa shapefile.shp

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import *
from mapit.areas.models import Area, Generation
from utils import save_polygons

class Command(LabelCommand):
    help = 'Creates Super Output Area boundaries from ONS shapefiles'
    args = '<ONS SOA shapefile>'

    lsoa_code_to_shape = {}

    def handle_label(self, filename, **options):
        print filename
        generation = Generation.objects.current()

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
            # skip if the SOA already exists in db (SOAs don't change)
            if Area.objects.filter(type=area_type, codes__code=lsoa_code).count():
                continue
            print "Adding %s (%s)" % (name, lsoa_code)
            m = Area(
                type = area_type,
                country = country,
                generation_low = generation,
                generation_high = generation,
            )
            m.save()
            poly = [ feat.geom ]
            m.names.update_or_create({ 'type': 'S' }, { 'name': name })
            self.lsoa_code_to_shape[lsoa_code] = (m, poly)
            m.codes.update_or_create({ 'type': 'ons' }, { 'code': lsoa_code })

        # save all the polygons once done
        save_polygons(self.lsoa_code_to_shape)

