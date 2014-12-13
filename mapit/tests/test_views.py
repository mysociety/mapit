import json

from django.test import TestCase
from django.conf import settings
from django.contrib.gis.geos import Polygon, Point

from mapit.models import Type, Area, Geometry, Generation, Postcode


class AreaViewsTest(TestCase):
    def setUp(self):
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

        polygon = Polygon(((-5, 50), (-5, 55), (1, 55), (1, 50), (-5, 50)), srid=4326)
        polygon.transform(settings.MAPIT_AREA_SRID)
        self.big_shape = Geometry.objects.create(
            area=self.big_area, polygon=polygon)

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

        polygon = Polygon(((-4, 51), (-4, 52), (-3, 52), (-3, 51), (-4, 51)), srid=4326)
        polygon.transform(settings.MAPIT_AREA_SRID)
        self.small_shape_1 = Geometry.objects.create(
            area=self.small_area_1, polygon=polygon)

        polygon = Polygon(((-3, 51), (-3, 52), (-2, 52), (-2, 51), (-3, 51)), srid=4326)
        polygon.transform(settings.MAPIT_AREA_SRID)
        self.small_shape_2 = Geometry.objects.create(
            area=self.small_area_2, polygon=polygon)

        self.postcode = Postcode.objects.create(
            postcode='P', location=Point(-3.5, 51.5))

    def test_areas_by_latlon(self):
        response = self.client.get('/point/latlon/51.5,-3.5.json')
        self.assertRedirects(response, '/point/4326/-3.5,51.5.json')

    def test_areas_by_point(self):
        url = '/point/4326/-3.4,51.5.json'
        response = self.client.get(url)

        content = json.loads(response.content.decode('utf-8'))

        self.assertEqual(
            set((int(x) for x in content.keys())),
            set((x.id for x in (self.big_area, self.small_area_1)))
            )

    def test_front_page(self):
        response = self.client.get('/')
        self.assertContains(response, 'MapIt')

    def test_json_links(self):
        id = self.big_area.id
        url = '/area/%d/covers.html?type=SML' % id
        response = self.client.get(url)
        self.assertContains(response, '/area/%d/covers?type=SML' % id)

    def test_example_postcode(self):
        id = self.small_area_1.id
        url = '/area/%d/example_postcode' % id
        response = self.client.get(url)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content, self.postcode.postcode)
