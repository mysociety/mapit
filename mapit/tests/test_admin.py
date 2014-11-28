from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.six import assertRegex


class AdminViewsTest(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_user('superuser', '', 'password')
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        self.client.login(username=self.superuser.username, password='password')

    def tearDown(self):
        self.client.logout()

    def test_admin_homepage(self):
        admin_url = reverse("admin:index")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)

    def test_area_admin_page(self):
        admin_url = reverse("admin:mapit_area_add")
        resp = self.client.get(admin_url)
        assertRegex(self, resp.content.decode('utf-8'), '<input([^>]*(id="id_name"|name="name"|type="text")){3}')
        self.assertEqual(resp.status_code, 200)

    def test_type_admin_page(self):
        admin_url = reverse("admin:mapit_type_add")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)

    def test_nametype_admin_page(self):
        admin_url = reverse("admin:mapit_nametype_add")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)

    def test_codetype_admin_page(self):
        admin_url = reverse("admin:mapit_codetype_add")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)

    def test_generation_admin_page(self):
        admin_url = reverse("admin:mapit_generation_add")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)

    def test_country_admin_page(self):
        admin_url = reverse("admin:mapit_country_add")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)

    def test_postcode_admin_page(self):
        admin_url = reverse("admin:mapit_postcode_add")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)
