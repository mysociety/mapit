import os

from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.conf import settings
from django.utils.six import StringIO

from ..models import Type, NameType, Area, Generation, Country


class MapitImportTest(TestCase):
    """Test the mapit_import management command"""

    def setUp(self):
        # Create a country, generation, area type and a name type for the
        # areas we'll load in from the KML file
        self.england = Country.objects.create(code="E", name="England")
        self.generation = Generation.objects.create(
            active=True,
            description="Test generation",
        )
        self.big_type = Type.objects.create(
            code="BIG",
            description="A large test area",
        )
        self.os_name_type = NameType.objects.create(
            code='O',
            description="Ordnance Survey name",
        )

    def test_loads_kml_files(self):
        # Assert no areas in db before
        self.assertEqual(Area.objects.count(), 0)



        # Load in the KML file
        fixtures_dir = os.path.join(settings.BASE_DIR, 'mapit', 'tests', 'fixtures')
        call_command(
            'mapit_import',
            os.path.join(fixtures_dir, 'example.kml'),
            country_code=self.england.code,
            generation_id=self.generation.id,
            area_type_code=self.big_type.code,
            name_type_code=self.os_name_type.code,
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
        self.assertEqual(area.country.name, self.england.name)
        self.assertEqual(area.generation_low.id, self.generation.id)
        self.assertEqual(area.generation_high.id, self.generation.id)
        self.assertEqual(area.type.code, "BIG")

    def test_reports_encoding_errors(self):
        # Load in a badly encoded file (it contains Windows charset encoded
        # apostrophe's, but reports itself as being UTF-8)
        fixtures_dir = os.path.join(settings.BASE_DIR, 'mapit', 'tests', 'fixtures')
        with self.assertRaises(CommandError) as context:
            call_command(
                'mapit_import',
                os.path.join(fixtures_dir, 'bad_encoding.shp'),
                country_code=self.england.code,
                generation_id=self.generation.id,
                area_type_code=self.big_type.code,
                name_type_code=self.os_name_type.code,
                commit=True,
                # These keep the commands quiet, comment out if you're debugging
                stderr=StringIO(),
                stdout=StringIO(),
            )
            # Previously, this would have been a message about not being able
            # to find the name field.
            expected_message = "Could not decode name using encoding 'utf-8' - is it in another encoding? \nSpecify one with --encoding"
            self.assertEqual(context.exception.message, expected_message)
