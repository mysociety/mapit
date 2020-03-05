# This script is used to import boundary polygons and other information
# from shapefiles representing areas of census geography

# Run as: ./manage.py mapit_UK_import_soa_2011 shapefile.shp --type=lsoa
# --commit

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from mapit.models import Area, Generation, Country, Type, NameType, CodeType
from django.conf import settings
from enum import Enum


class GeographyType(Enum):
    """
    allowed geographic imports
    """
    lsoa = "lsoa"
    msoa = "msoa"
    soa = "soa"
    dz = "dz"
    lz = "lz"

    def __str__(self):
        return self.value


class Command(LabelCommand):
    help = 'Creates Super Output Area boundaries from ONS/Scot Gov/OSNI shapefiles'
    label = '<ONS SOA shapefile>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true',
                            dest='commit', help='Actually update the database')
        parser.add_argument('--type', dest='file_type', help="options: lsoa, msoa, soa, dz, lz",
                            type=GeographyType, choices=list(GeographyType)
                            )
        parser.add_argument('--generalized', action='store_true',
                            dest='generalized', help='Is shape generalised?')

    def handle_label(self, filename, **options):
        print(filename)
        generation = Generation.objects.new()

        file_type = options["file_type"].value.lower()
        generalized = options["generalized"]

        if file_type == "lsoa":  # England and Wales
            feat_name = 'LSOA11NM'
            feat_code = 'LSOA11CD'
        elif file_type == "msoa":  # England and Wales
            feat_name = 'MSOA11NM'
            feat_code = 'MSOA11CD'
        elif file_type == "soa":  # super output areas - NI
            feat_name = 'SOA_LABEL'
            feat_code = 'SOA_CODE'
        elif file_type == "dz":  # datazone - scotland
            feat_name = 'Name'
            feat_code = 'DataZone'
        elif file_type == "iz":  # intermediate zone - scotland
            feat_name = 'Name'
            feat_code = 'InterZone'
        else:
            raise Exception(
                "Need to specify a small area type (lsoa, dz, soa, lz, msoa)")

        if file_type in ["lsoa", "dz", "soa"]:
            area_type = 'OLF'
        elif file_type in ["msoa", "iz"]:
            area_type = 'OMF'

        if generalized:
            area_type = area_type[:2] + "G"

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            # retrieve name and code, and set country
            name = feat[feat_name].value
            lsoa_code = feat[feat_code].value
            if lsoa_code[:2] == "95":
                country = "N"
            else:
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
            if options['commit']:
                m.save()
                m.names.update_or_create(type=NameType.objects.get(
                    code='S'), defaults={'name': name})
                m.codes.update_or_create(type=CodeType.objects.get(
                    code='ons'), defaults={'code': lsoa_code})

            p = feat.geom

            # convert ni to same map system
            if file_type == "soa":
                p.srid = 29902
                if not(p.srid == settings.MAPIT_AREA_SRID):
                    p.transform(settings.MAPIT_AREA_SRID)

            if p.geom_name == 'POLYGON':
                shapes = [p]
            else:
                shapes = p
            for g in shapes:
                if options['commit']:
                    m.polygons.create(polygon=g.wkt)
