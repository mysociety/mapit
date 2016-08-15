# This script is used to import information from the Northern Ireland
# Output Areas, available from http://www.nisra.gov.uk/geography/default.asp2.htm

from django.core.management.base import LabelCommand
# Not using LayerMapping as want more control, but what it does is what this does
# from django.contrib.gis.utils import LayerMapping
from django.contrib.gis.gdal import DataSource

from mapit.models import Area, Generation, Country, Type, CodeType, NameType
from mapit.management.command_utils import save_polygons


class Command(LabelCommand):
    help = 'Import NI Output Areas'
    args = '<NI Super Output Area shapefile> <NI Output Area shapefile>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    ons_code_to_shape = {}
    councils = []

    def handle_label(self, filename, **options):
        country = Country.objects.get(code='N')
        oa_type = Type.objects.get(code='OUA')
        soa_type = Type.objects.get(code='OLF')
        name_type = NameType.objects.get(code='S')
        code_type = CodeType.objects.get(code='ons')

        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        # Compile an alphabetical list of NI councils and their wards, OA codes
        # are assigned alphabetically.
        if not self.councils:
            self.councils = Area.objects.filter(type=Type.objects.get(code='LGD')).order_by('name').values()
            for lgd in self.councils:
                lges = Area.objects.filter(parent_area=lgd['id'])
                areas = []
                for lge in lges:
                    lgws = Area.objects.filter(parent_area=lge).values()
                    areas += lgws
                lgd['wards'] = sorted(areas, key=lambda x: x['name'])

        ds = DataSource(filename)
        layer = ds[0]
        layer_name = str(layer)
        for feat in layer:
            if layer_name == 'soa':
                area_type = soa_type
                ons_code = feat['SOA_CODE'].value
                name = feat['SOA_LABEL'].value.replace('_', ' ')
            elif layer_name == 'OA_ni':
                area_type = oa_type
                ons_code = feat['OA_CODE'].value
                name = 'Output Area %s' % ons_code
            else:
                raise Exception('Bad data passed in')

            council = ord(ons_code[2:3]) - 65
            ward = int(ons_code[4:6]) - 1
            if ward == 98:  # SOA covers two wards, set parent to council, best we can do
                parent = self.councils[council]['id']
            else:
                parent = self.councils[council]['wards'][ward]['id']

            try:
                m = Area.objects.get(codes__type=code_type, codes__code=ons_code)
                if int(options['verbosity']) > 1:
                    print("  Area matched, %s" % (m, ))
            except Area.DoesNotExist:
                print("  New area: %s" % (ons_code))
                m = Area(
                    name=name,  # If committing, this will be overwritten by the m.names.update_or_create
                    type=area_type,
                    country=country,
                    parent_area_id=parent,
                    generation_low=new_generation,
                    generation_high=new_generation,
                )

            if m.generation_high and current_generation and m.generation_high.id < current_generation.id:
                raise Exception("Area %s found, but not in current generation %s" % (m, current_generation))
            m.generation_high = new_generation
            m.parent_area_id = parent
            if options['commit']:
                m.save()

            f = feat.geom
            f.srid = 29902
            poly = [f]

            if options['commit']:
                m.names.update_or_create(type=name_type, defaults={'name': name})
            if ons_code:
                self.ons_code_to_shape[ons_code] = (m, poly)
                if options['commit']:
                    m.codes.update_or_create(type=code_type, defaults={'code': ons_code})

        if options['commit']:
            save_polygons(self.ons_code_to_shape)
