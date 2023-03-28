import os
from django.contrib.gis.gdal import DataSource
from mapit.models import Area
from ..structural_changes import Command as BaseCommand


class Command(BaseCommand):
    counties = {
        "Cumbria County Council": (
            "Allerdale Borough Council",
            "Carlisle City Council",
            "Copeland Borough Council",
            "Barrow-in-Furness Borough Council",
            "Eden District Council",
            "South Lakeland District Council",
        ),
        "North Yorkshire County Council": (
            "Selby District Council",
            "Harrogate Borough Council",
            "Craven District Council",
            "Richmondshire District Council",
            "Hambleton District Council",
            "Ryedale District Council",
            "Scarborough Borough Council",
        ),
        "Somerset County Council": (
            "Mendip District Council",
            "Sedgemoor District Council",
            "Somerset West and Taunton District Council",
            "South Somerset District Council",
        ),
    }

    new_utas = (
        ('Cumberland', 'E06000063', (
            "Allerdale Borough Council",
            "Carlisle City Council",
            "Copeland Borough Council",
        )),
        ('Westmorland and Furness', 'E06000064', (
            "Barrow-in-Furness Borough Council",
            "Eden District Council",
            "South Lakeland District Council",
        )),
        ("North Yorkshire County Council", "E06000065", (
            "Selby District Council",
            "Harrogate Borough Council",
            "Craven District Council",
            "Richmondshire District Council",
            "Hambleton District Council",
            "Ryedale District Council",
            "Scarborough Borough Council",
        )),
        ("Somerset County Council", "E06000066", (
            "Mendip District Council",
            "Sedgemoor District Council",
            "Somerset West and Taunton District Council",
            "South Somerset District Council",
        )),
    )

    shapefiles = (
        'Cumberland_interim_Wards.shp',
        'Westmorland_and_Furness_interim_wards.shp',
        'North_Yorkshire_interim_Electoral_Divisions.shp',
        'Somerset_interim_Electoral_Divisions.shp',
    )

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('boundaries', help='Pass in the directory containing the shapefiles provided by OS')

    def handle(self, *args, **options):
        self.directory = options['boundaries']
        self.verbosity = int(options['verbosity'])
        super().handle(*args, **options)

    def create_new_unitaries(self):
        """New areas come from passed in shapefiles manually sent to us by OS"""

        # First the new councils themselves
        for new_uta in self.new_utas:
            area = Area.objects.filter(type__code='DIS', name__in=new_uta[2], generation_high=self.g)
            self._create(new_uta[0], 'UTA', area, new_uta[1])

        # And now their wards
        for filename in self.shapefiles:
            ds = DataSource(os.path.join(self.directory, filename))
            layer = ds[0]
            for feat in layer:
                name = feat['WD22NM'].value or ''
                ons_code = feat['WD22CD'].value
                try:
                    m = Area.objects.get(codes__type=self.code_type, codes__code=ons_code)
                    if self.verbosity > 1:
                        print("  Area matched, %s" % (m, ))
                except Area.DoesNotExist:
                    self._create(name, 'UTW', feat.geom, ons_code)
