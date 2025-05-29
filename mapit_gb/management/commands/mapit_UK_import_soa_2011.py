# This script is used to import boundary polygons and other information
# from shapefiles representing areas of census geography

# Run as: ./manage.py mapit_UK_import_soa_2011 shapefile.shp --type=lsoa
# --commit

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from mapit.models import Area, Generation, Country, Type, NameType, CodeType
from django.conf import settings
from enum import Enum
from mapit.management.command_utils import save_polygons


class GeographyType(Enum):
    """
    allowed geographic imports
    """
    lsoa = "lsoa"
    msoa = "msoa"
    soa = "soa"
    dz = "dz"
    iz = "iz"

    def __str__(self):
        return self.value


class Command(LabelCommand):
    help = 'Creates Super Output Area boundaries from ONS/Scot Gov/OSNI shapefiles'
    label = '<ONS SOA shapefile>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true',
                            dest='commit', help='Actually update the database')
        parser.add_argument('--type', dest='file_type', help="options: lsoa, msoa, soa, dz, iz",
                            type=GeographyType, choices=list(GeographyType)
                            )
        parser.add_argument('--generalized', action='store_true',
                            dest='generalized', help='Is shape generalised?')

    def handle_label(self, filename, **options):
        self.stdout.write("Importing from %s" % filename)

        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()

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
                "Need to specify a small area type (lsoa, dz, soa, iz, msoa)")

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
            code = feat[feat_code].value
            if code[:2] == "95":
                country = "N"
            else:
                country = code[0]

            self.stdout.write("  looking at '%s' (%s)" % (name, code))

            g = feat.geom.transform(settings.MAPIT_AREA_SRID, clone=True)

            # skip if the SOA already exists in db (SOAs don't change)
            areas = Area.objects.filter(type__code=area_type, codes__code=code)
            if len(areas):
                m = areas[0]
                # check that we are not about to skip a generation
                if m.generation_high and current_generation and m.generation_high.id < current_generation.id:
                    raise Exception("Area %s found, but not in current generation %s" % (m, current_generation))
                if m.generation_high != new_generation and options['commit']:
                    m.generation_high = new_generation
                    m.save()
                continue

            print("Adding %s (%s) %s" % (name, code, feat.geom.geom_name))
            m = Area(
                name=name,
                type=Type.objects.get(code=area_type),
                country=Country.objects.get(code=country),
                generation_low=new_generation,
                generation_high=new_generation,
            )

            poly = [g] if g is not None else []

            if options['commit']:
                m.save()
                m.names.update_or_create(type=NameType.objects.get(
                    code='S'), defaults={'name': name})
                m.codes.update_or_create(type=CodeType.objects.get(
                    code='ons'), defaults={'code': code})
                save_polygons({m.id: (m, poly)})
