import json

from django.test import TestCase
from django.contrib.gis.geos import Polygon

import settings

from mapit.models import Type, Area, Geometry, Generation

class AreaViewsTest(TestCase):
    @classmethod
    def setUpClass(self):
        self.old_srid = settings.MAPIT_AREA_SRID
        settings.MAPIT_AREA_SRID = 4326

        self.generation = Generation.objects.create(
            active=True,
            description="Test generation",
            )

        self.big_type = Type.objects.create(
            code="BIG",
            description="A large test area",
            )
        
        self.small_type = Type.objects.create(
            code="SML",
            description="A small test area",
            )

        self.big_area = Area.objects.create(
            name="Big Area",
            type=self.big_type,
            generation_low=self.generation,
            generation_high=self.generation,
            )

        self.big_shape = Geometry.objects.create(
            area=self.big_area,
            polygon=Polygon(((-5, 50), (-5, 55), (1, 55), (1, 50), (-5, 50))),
            )

        self.small_area_1 = Area.objects.create(
            name="Small Area 1",
            type=self.small_type,
            generation_low=self.generation,
            generation_high=self.generation,
            )

        self.small_area_2 = Area.objects.create(
            name="Small Area 2",
            type=self.small_type,
            generation_low=self.generation,
            generation_high=self.generation,
            )

        self.small_shape_1 = Geometry.objects.create(
            area=self.small_area_1,
            polygon=Polygon(((-4, 51), (-4, 52), (-3, 52), (-3, 51), (-4, 51))),
            )

        self.small_shape_2 = Geometry.objects.create(
            area=self.small_area_2,
            polygon=Polygon(((-3, 51), (-3, 52), (-2, 52), (-2, 51), (-3, 51))),
            )

    def test_areas_by_latlon(self):
        response = self.client.get('/point/latlon/51.5,-3.5.json')
        self.assertRedirects(response, '/point/4326/-3.5,51.5.json')

    def test_areas_by_point(self):
        # Different co-ords to evade any caching
        response = self.client.get('/point/4326/-3.4,51.5.json')

        content = json.loads(response.content)

        self.assertEqual(
            set((int(x) for x in content.keys())),
            set((x.id for x in (self.big_area, self.small_area_1)))
            )

    def test_front_page(self):
        response = self.client.get('/')

    @classmethod
    def tearDownClass(self):
        settings.MAPIT_AREA_SRID = self.old_srid
