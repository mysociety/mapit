import os

from django.test import TestCase
from django.core.management import call_command
from django.conf import settings
from django.utils.six import StringIO
from django.contrib.gis.gdal.prototypes import ds

from ..models import Type, NameType, Area, Generation, Country


class MapitImportTest(TestCase):
    """Test the mapit_import management command"""

    def setUp(self):
        # Forcefully register a GDAL datasource driver, because Django has a
        # bug where it assumes that any existing drivers mean they're all
        # available, which doesn't seem to be the case.
        if not ds.get_driver_count():
            ds.register_all()

    def test_loads_kml_files(self):
        # Assert no areas in db before
        self.assertEqual(Area.objects.count(), 0)

        # Create a country, generation, area type and a name type for the
        # areas we'll load in from the KML file
        england = Country.objects.create(code="E", name="England")
        generation = Generation.objects.create(
            active=True,
            description="Test generation",
        )
        big_type = Type.objects.create(
            code="BIG",
            description="A large test area",
        )
        os_name_type = NameType.objects.create(
            code='O',
            description="Ordnance Survey name",
        )

        # Load in the KML file
        fixtures_dir = os.path.join(settings.BASE_DIR, 'mapit', 'tests', 'fixtures')
        call_command(
            'mapit_import',
            os.path.join(fixtures_dir, 'example.kml'),
            country_code=england.code,
            generation_id=generation.id,
            area_type_code=big_type.code,
            name_type_code=os_name_type.code,
            commit=True,
            # These keep the commands quiet, comment out if you're debugging
            stderr=StringIO(),
            stdout=StringIO(),
        )

        # Check that the area in the KML file are now in the db
        self.assertEqual(Area.objects.count(), 1)

        # Check it loaded the data properly
        area = Area.objects.all()[0]
        self.assertEqual(area.name, "London")
        self.assertEqual(area.country.name, england.name)
        self.assertEqual(area.generation_low.id, generation.id)
        self.assertEqual(area.generation_high.id, generation.id)
        self.assertEqual(area.type.code, "BIG")
