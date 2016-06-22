from django.conf import settings
from django.test import TestCase
from django.contrib.gis.geos import Polygon, Point
from django.utils.six.moves import urllib

from mapit import utils, models

from mapit_gb import countries
from mapit.tests.utils import get_content


def url_postcode(pc):
    return urllib.parse.quote(countries.get_postcode_display(pc))


class GBViewsTest(TestCase):
    def setUp(self):
        # Make sure we're using the GB postcode functions here
        models.countries = countries
        utils.countries = countries

        self.postcode = models.Postcode.objects.create(
            postcode='SW1A1AA',
            location=Point(-0.141588, 51.501009)
        )

        self.generation = models.Generation.objects.create(
            active=True,
            description="Test generation",
        )

        self.type = models.Type.objects.create(
            code="TEST_TYPE",
            description="A test area",
        )

        self.area = models.Area.objects.create(
            name="Area",
            type=self.type,
            generation_low=self.generation,
            generation_high=self.generation,
        )

        code_type = models.CodeType.objects.create(
            code='CodeType',
            description='CodeType description',
        )
        models.Code.objects.create(
            area=self.area,
            type=code_type,
            code='CODE',
        )

        polygon = Polygon(((-5, 50), (-5, 55), (1, 55), (1, 50), (-5, 50)), srid=4326)
        polygon.transform(settings.MAPIT_AREA_SRID)
        self.shape = models.Geometry.objects.create(
            area=self.area, polygon=polygon,
        )

        code_type_gss = models.CodeType.objects.create(
            code='gss',
            description='GSS codes from ONS',
        )
        models.Code.objects.create(
            area=self.area,
            type=code_type_gss,
            code='E05000025',
        )

    def test_postcode_json(self):
        pc = self.postcode.postcode
        url = '/postcode/%s' % urllib.parse.quote(pc)
        response = self.client.get(url)
        content = get_content(response)

        in_gb_coords = self.postcode.location.transform(27700, clone=True)
        pc = countries.get_postcode_display(self.postcode.postcode)
        self.assertDictEqual(content, {
            'postcode': pc,
            'wgs84_lat': self.postcode.location.y,
            'wgs84_lon': self.postcode.location.x,
            'coordsyst': 'G',
            'easting': round(in_gb_coords.x),
            'northing': round(in_gb_coords.y),
            'areas': {
                str(self.area.id): {
                    'id': self.area.id,
                    'name': self.area.name,
                    'parent_area': None,
                    'type': self.type.code,
                    'type_name': self.type.description,
                    'generation_low': self.generation.id,
                    'generation_high': self.generation.id,
                    'country': '',
                    'country_name': '-',
                    'codes': {
                        'CodeType': 'CODE',
                        'gss': 'E05000025',
                    },
                    'all_names': {},
                }
            }
        })

    def test_postcode_json_link(self):
        pc = self.postcode.postcode
        url = '/postcode/%s.html' % urllib.parse.quote(pc)
        response = self.client.get(url)
        self.assertContains(response, '"/postcode/%s"' % url_postcode(pc))

    def test_partial_json(self):
        url = '/postcode/partial/SW1A'
        response = self.client.get(url)
        content = get_content(response)
        countries.get_postcode_display(self.postcode.postcode)
        in_gb_coords = self.postcode.location.transform(27700, clone=True)
        self.assertDictEqual(content, {
            'wgs84_lat': self.postcode.location.y,
            'wgs84_lon': self.postcode.location.x,
            'coordsyst': 'G',
            'postcode': 'SW1A',
            'easting': round(in_gb_coords.x),
            'northing': round(in_gb_coords.y)
        })

    def test_partial_json_link(self):
        url = '/postcode/partial/SW1A.html'
        response = self.client.get(url)
        self.assertContains(response, '"/postcode/partial/SW1A"')

    def test_nearest_json(self):
        url = '/nearest/4326/%f,%f' % self.postcode.location.coords
        response = self.client.get(url)
        content = get_content(response)
        pc = countries.get_postcode_display(self.postcode.postcode)
        in_gb_coords = self.postcode.location.transform(27700, clone=True)
        self.assertDictEqual(content, {
            'postcode': {
                'distance': 0,
                'wgs84_lat': self.postcode.location.y,
                'wgs84_lon': self.postcode.location.x,
                'coordsyst': 'G',
                'postcode': pc,
                'easting': round(in_gb_coords.x),
                'northing': round(in_gb_coords.y)
            }
        })

    def test_nearest_json_link(self):
        url = '/nearest/4326/%f,%f.html' % self.postcode.location.coords
        response = self.client.get(url)
        pc = self.postcode.postcode
        self.assertContains(response, '"/postcode/%s"' % url_postcode(pc))

    def test_gss_code(self):
        response = self.client.get('/area/E05000025')
        self.assertRedirects(response, '/area/%d' % self.area.id)

        response = self.client.get('/area/E05000025.geojson')
        self.assertRedirects(response, '/area/%d.geojson' % self.area.id)
