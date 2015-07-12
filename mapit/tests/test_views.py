import json

from django.test import TestCase
from django.conf import settings
from django.contrib.gis.geos import Polygon, Point

from mapit.models import Type, Area, Geometry, Generation, Postcode
from mapit.tests.utils import get_content


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
        response = self.client.get(url, HTTP_ACCEPT_ENCODING='gzip')

        content = get_content(response)

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
        content = get_content(response)
        self.assertEqual(content, self.postcode.postcode)

    def test_nearest_with_bad_srid(self):
        url = '/nearest/84/0,0.json'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(content, {
            'code': 400, 'error': 'GetProj4StringSPI: Cannot find SRID (84) in spatial_ref_sys\n'
        })

    def test_areas_polygon_valid(self):
        id1 = self.small_area_1.id
        id2 = self.small_area_2.id
        url = '/areas/%d,%d.geojson' % (id1, id2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = json.loads(response.content.decode('utf-8'))
        self.assertEqual(len(content), 2)

    def test_areas_polygon_one_id(self):
        id = self.small_area_1.id

        url_area = '/area/%d.geojson' % id
        response_area = self.client.get(url_area)
        self.assertEqual(response_area.status_code, 200)
        content_area = json.loads(response_area.content.decode('utf-8'))

        url_areas = '/areas/%d.geojson' % id
        response_areas = self.client.get(url_areas)
        self.assertEqual(response_areas.status_code, 200)
        content_areas = json.loads(response_areas.content.decode('utf-8'))

        self.assertEqual(content_area, content_areas['features'][0]['geometry'])
        self.assertEqual(content_areas['type'], 'FeatureCollection')

    def test_areas_polygon_bad_params(self):
        url = '/areas/99999.geojson'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        id = self.small_area_1.id
        url = '/areas/%d.geojson?simplify_tolerance=a' % id
        response = self.client.get(url)
        self.assertEqual(response.status_code, 400)
