# coding=utf-8

from django.test import TestCase
from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.utils.encoding import smart_text

from mapit.models import Type, Area, Generation, Name, NameType
import mapit_gb.countries
import mapit.models


class NamesTest(TestCase):
    def setUp(self):
        self.generation = Generation.objects.create(
            active=True,
            description="Test generation",
        )

        self.area_type = Type.objects.create(
            code="BIG",
            description="A large test area",
        )

        self.name_type = NameType.objects.create(
            code='O',
            description='Ordnance Survey name type'
        )

        self.area = Area.objects.create(
            name="Big Area",
            type=self.area_type,
            generation_low=self.generation,
            generation_high=self.generation,
        )

        polygon = Polygon(((-5, 50), (-5, 55), (1, 55), (1, 50), (-5, 50)), srid=4326)
        polygon.transform(settings.MAPIT_AREA_SRID)
        self.geometry = self.area.polygons.create(polygon=polygon)

    def test_new_name_changes_area_name_in_gb(self):
        """We can't use override_settings, as mapit.countries has been set
        based upon MAPIT_COUNTRY already in initial import"""
        mapit.models.countries = mapit_gb.countries
        Name.objects.create(name='New Name (B)', type=self.name_type, area=self.area)
        self.assertEqual(self.area.name, 'New Name Borough')

    def test_new_name_does_not_change_area_name_elsewhere(self):
        mapit.models.countries = None
        Name.objects.create(name='New Name', type=self.name_type, area=self.area)
        self.assertEqual(self.area.name, 'Big Area')

    def test_geometry_name_works(self):
        name = smart_text('Big “Area”')
        self.area.name = name
        self.area.save()
        should_be = '%s %s, polygon %d' % (self.area_type.code, name, self.geometry.id)
        self.assertEqual(smart_text(self.geometry), should_be)
