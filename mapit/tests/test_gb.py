import urllib

from django.test import TestCase

from mapit import utils, models

# Make sure we're using the GB postcode functions here
from mapit_gb import countries
utils.countries = countries
models.countries = countries

class AreaViewsTest(TestCase):
    def setUp(self):
        self.postcode = models.Postcode.objects.create(postcode='SW1A1AA', location='POINT(0 0)')

    def test_postcode_json_link(self):
        pc = self.postcode.postcode
        url = '/postcode/%s.html' % urllib.quote(pc)
        response = self.client.get(url)
        pc = urllib.quote(countries.get_postcode_display(pc))
        self.assertContains(response, '"/postcode/%s"' % pc)

    def test_partial_json_link(self):
        url = '/postcode/partial/SW1A.html'
        response = self.client.get(url)
        self.assertContains(response, '"/postcode/partial/SW1A"')
