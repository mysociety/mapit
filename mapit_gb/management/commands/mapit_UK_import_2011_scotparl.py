# This script is used to import the 2011 Scottish Parliament from OS Boundary-Line.

import re

from django.core.management.base import LabelCommand
from django.contrib.gis.gdal import DataSource
from django.utils import six

from mapit.models import Area, Generation, Country, Type, CodeType, NameType
from mapit.management.command_utils import save_polygons

name_to_code = {
    'Aberdeen Central P Const': 'S16000074',
    'Aberdeen Donside P Const': 'S16000075',
    'Aberdeen South and North Kincardine P Const': 'S16000076',
    'Aberdeenshire East P Const': 'S16000077',
    'Aberdeenshire West P Const': 'S16000078',
    'Airdrie and Shotts P Const': 'S16000079',
    'Almond Valley P Const': 'S16000080',
    'Angus North and Mearns P Const': 'S16000081',
    'Angus South P Const': 'S16000082',
    'Argyll and Bute P Const': 'S16000083',
    'Ayr P Const': 'S16000084',
    'Banffshire and Buchan Coast P Const': 'S16000085',
    'Caithness, Sutherland and Ross P Const': 'S16000086',
    'Carrick, Cumnock and Doon Valley P Const': 'S16000087',
    'Clackmannanshire and Dunblane P Const': 'S16000088',
    'Clydebank and Milngavie P Const': 'S16000089',
    'Clydesdale P Const': 'S16000090',
    'Coatbridge and Chryston P Const': 'S16000091',
    'Cowdenbeath P Const': 'S16000092',
    'Cumbernauld and Kilsyth P Const': 'S16000093',
    'Cunninghame North P Const': 'S16000094',
    'Cunninghame South P Const': 'S16000095',
    'Dumbarton P Const': 'S16000096',
    'Dumfriesshire P Const': 'S16000097',
    'Dundee City East P Const': 'S16000098',
    'Dundee City West P Const': 'S16000099',
    'Dunfermline P Const': 'S16000100',
    'East Kilbride P Const': 'S16000101',
    'East Lothian P Const': 'S16000102',
    'Eastwood P Const': 'S16000103',
    'Edinburgh Central P Const': 'S16000104',
    'Edinburgh Eastern P Const': 'S16000105',
    'Edinburgh Northern and Leith P Const': 'S16000106',
    'Edinburgh Pentlands P Const': 'S16000107',
    'Edinburgh Southern P Const': 'S16000108',
    'Edinburgh Western P Const': 'S16000109',
    'Na h-Eileanan an Iar P Const': 'S16000110',
    'Ettrick, Roxburgh and Berwickshire P Const': 'S16000111',
    'Falkirk East P Const': 'S16000112',
    'Falkirk West P Const': 'S16000113',
    'Galloway and West Dumfries P Const': 'S16000114',
    'Glasgow Anniesland P Const': 'S16000115',
    'Glasgow Cathcart P Const': 'S16000116',
    'Glasgow Kelvin P Const': 'S16000117',
    'Glasgow Maryhill and Springburn P Const': 'S16000118',
    'Glasgow Pollok P Const': 'S16000119',
    'Glasgow Provan P Const': 'S16000120',
    'Glasgow Shettleston P Const': 'S16000121',
    'Glasgow Southside P Const': 'S16000122',
    'Greenock and Inverclyde P Const': 'S16000123',
    'Hamilton, Larkhall and Stonehouse P Const': 'S16000124',
    'Inverness and Nairn P Const': 'S16000125',
    'Kilmarnock and Irvine Valley P Const': 'S16000126',
    'Kirkcaldy P Const': 'S16000127',
    'Linlithgow P Const': 'S16000128',
    'Mid Fife and Glenrothes P Const': 'S16000129',
    'Midlothian North and Musselburgh P Const': 'S16000130',
    'Midlothian South, Tweeddale and Lauderdale P Const': 'S16000131',
    'Moray P Const': 'S16000132',
    'Motherwell and Wishaw P Const': 'S16000133',
    'North East Fife P Const': 'S16000134',
    'Orkney Islands P Const': 'S16000135',
    'Paisley P Const': 'S16000136',
    'Perthshire North P Const': 'S16000137',
    'Perthshire South and Kinrossshire P Const': 'S16000138',
    'Renfrewshire North and West P Const': 'S16000139',
    'Renfrewshire South P Const': 'S16000140',
    'Rutherglen P Const': 'S16000141',
    'Shetland Islands P Const': 'S16000142',
    'Skye, Lochaber and Badenoch P Const': 'S16000143',
    'Stirling P Const': 'S16000144',
    'Strathkelvin and Bearsden P Const': 'S16000145',
    'Uddingston and Bellshill P Const': 'S16000146',
    'Central Scotland PER': 'S17000009',
    'Glasgow PER': 'S17000010',
    'Highland and Islands PER': 'S17000011',
    'Lothian PER': 'S17000012',
    'Mid Scotland and Fife PER': 'S17000013',
    'North East Scotland PER': 'S17000014',
    'South Scotland PER': 'S17000015',
    'West of Scotland PER': 'S17000016',
}


class Command(LabelCommand):
    help = 'Import OS Boundary-Line Scottish Parliament 2011 in advance'
    args = '<Boundary-Line SHP files>'

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    ons_code_to_shape = {}

    def handle_label(self, filename, **options):
        print(filename)
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        name_type = NameType.objects.get(code='O')
        code_type = CodeType.objects.get(code='gss')

        ds = DataSource(filename)
        layer = ds[0]
        for feat in layer:
            name = feat['NAME'].value
            if not isinstance(name, six.text_type):
                name = name.decode('iso-8859-1')
            print("  %s" % name)
            name = re.sub('\s*\(DET( NO \d+|)\)\s*(?i)', '', name)
            name = re.sub('\s+', ' ', name)

            if "P Const" in name:
                area_code = 'SPC'
            elif "PER" in name:
                area_code = 'SPE'
            else:
                raise Exception("Unknown type of area %s" % name)

            ons_code = name_to_code[name]

            if ons_code in self.ons_code_to_shape:
                m, poly = self.ons_code_to_shape[ons_code]
                if options['commit']:
                    m_name = m.names.get(type=name_type).name
                    if name != m_name:
                        raise Exception("ONS code %s is used for %s and %s" % (ons_code, name, m_name))
                # Otherwise, combine the two shapes for one area
                print("    Adding subsequent shape to ONS code %s" % ons_code)
                poly.append(feat.geom)
                continue

            try:
                m = Area.objects.get(codes__type=code_type, codes__code=ons_code)
            except Area.DoesNotExist:
                m = Area(
                    type=Type.objects.get(code=area_code),
                    country=Country.objects.get(name='Scotland'),
                    generation_low=new_generation,
                    generation_high=new_generation,
                )

            if options['commit']:
                m.save()

            poly = [feat.geom]

            if options['commit']:
                m.names.update_or_create(type=name_type, defaults={'name': name})
            if ons_code:
                self.ons_code_to_shape[ons_code] = (m, poly)
                if options['commit']:
                    m.codes.update_or_create(type=code_type, defaults={'code': ons_code})

        if options['commit']:
            save_polygons(self.ons_code_to_shape)
