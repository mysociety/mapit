# This script is used to import boundary polygons and other information
# from the ONS's CD-ROM of Super Output Areas for England and Wales.
# Information about the CD-ROM here: http://bit.ly/63bX97

# Run as: ./manage.py mapit_UK_import_soa shapefile.shp

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from mapit.models import Area, Generation, Country, Type, NameType, CodeType


class Command(LabelCommand):
    help = 'Creates Super Output Area boundaries from ONS shapefiles'
    args = '<ONS SOA shapefile>'

    def handle_label(self, filename, **options):
        print(filename)
        generation = Generation.objects.current()

        short_filename = filename.split("/")[-1]
        filename_prefix = short_filename[:4]
        filename_suffix = short_filename.split(".")[0][-3:]

        # check shapefile type - we handle both LSOA and MSOA
        if filename_prefix == "LSOA":
            feat_name = 'LSOA04NM'
            feat_code = 'LSOA04CD'
            if filename_suffix == 'BGC':
                area_type = 'OLG'
            else:
                area_type = 'OLF'
        elif filename_prefix == "MSOA":
            feat_name = 'MSOA04NM'
            feat_code = 'MSOA04CD'
            if filename_suffix == 'BGC':
                area_type = 'OMG'
            else:
                area_type = 'OMF'
        else:
            raise Exception("Sorry, this script only handles LSOA/MSOA shapefiles!")

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            # retrieve name and code, and set country
            name = feat[feat_name].value
            lsoa_code = feat[feat_code].value
            country = lsoa_code[0]
            # skip if the SOA already exists in db (SOAs don't change)
            if Area.objects.filter(type__code=area_type, codes__code=lsoa_code).count():
                continue
            print("Adding %s (%s) %s" % (name, lsoa_code, feat.geom.geom_name))
            m = Area(
                type=Type.objects.get(code=area_type),
                country=Country.objects.get(code=country),
                generation_low=generation,
                generation_high=generation,
            )
            m.save()
            m.names.update_or_create(type=NameType.objects.get(code='S'), defaults={'name': name})
            m.codes.update_or_create(type=CodeType.objects.get(code='ons'), defaults={'code': lsoa_code})

            p = feat.geom
            if p.geom_name == 'POLYGON':
                shapes = [p]
            else:
                shapes = p
            for g in shapes:
                m.polygons.create(polygon=g.wkt)
