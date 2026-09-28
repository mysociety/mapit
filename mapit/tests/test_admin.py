from django.conf import settings
from django.contrib.gis.geos import Polygon
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse

from mapit.models import Area, Code, CodeType, Generation, Geometry, GeometrySubdivided, Name, NameType, Type


class LoggedInSuperuserMixin(object):
    def setUp(self):
        super().setUp()
        self.superuser = User.objects.create_user('superuser', '', 'password')
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        self.client.login(username=self.superuser.username, password='password')

    def tearDown(self):
        self.client.logout()
        super().tearDown()


class AdminViewsTest(LoggedInSuperuserMixin, TestCase):
    def test_admin_homepage(self):
        admin_url = reverse("admin:index")
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)

    def test_area_admin_page(self):
        admin_url = reverse("admin:mapit_area_add")
        resp = self.client.get(admin_url)
        self.assertRegex(resp.content.decode('utf-8'), '<input([^>]*(id="id_name"|name="name"|type="text")){3}')
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


class AdminDeleteConfirmationTest(LoggedInSuperuserMixin, TestCase):
    def setUp(self):
        super().setUp()

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
        self.small_area = Area.objects.create(
            name="Small Area 1",
            type=self.small_type,
            parent_area=self.big_area,
            generation_low=self.generation,
            generation_high=self.generation,
        )

        polygon = Polygon(((-5, 50), (-5, 55), (1, 55), (1, 50), (-5, 50)), srid=4326)
        polygon.transform(settings.MAPIT_AREA_SRID)
        self.geometry = Geometry.objects.create(area=self.big_area, polygon=polygon)

        Name.objects.create(
            area=self.big_area,
            type=NameType.objects.create(code="G", description="Government"),
            name="New Name",
        )
        Code.objects.create(
            area=self.big_area,
            type=CodeType.objects.create(code="gss", description="GSS codes from ONS"),
            code="E05000025",
        )

    def test_area_delete_confirmation_is_just_area(self):
        admin_url = reverse("admin:mapit_area_delete", args=(self.big_area.id,))
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Big Area")
        self.assertNotContains(resp, "polygon")
        self.assertNotContains(resp, "New Name")
        self.assertNotContains(resp, "E05000025")
        self.assertNotContains(resp, "Small Area 1")

    def test_area_bulk_delete_confirmation_is_just_area(self):
        changelist_url = reverse("admin:mapit_area_changelist")
        resp = self.client.post(changelist_url, {
            'action': 'delete_selected',
            '_selected_action': [str(self.big_area.id)],
            })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Big Area")
        self.assertNotContains(resp, "polygon")
        self.assertNotContains(resp, "New Name")
        self.assertNotContains(resp, "E05000025")
        self.assertNotContains(resp, "Small Area 1")

    def test_area_delete_still_cascades(self):
        admin_url = reverse("admin:mapit_area_delete", args=(self.big_area.id,))
        resp = self.client.post(admin_url, {'post': 'yes'})
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(Area.objects.count(), 0)
        self.assertEqual(Geometry.objects.count(), 0)
        self.assertEqual(GeometrySubdivided.objects.count(), 0)
        self.assertEqual(Name.objects.count(), 0)
        self.assertEqual(Code.objects.count(), 0)

    def test_type_delete_confirmation_stops_at_area(self):
        admin_url = reverse("admin:mapit_type_delete", args=(self.big_type.id,))
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "A large test area")
        self.assertContains(resp, "Big Area")
        self.assertNotContains(resp, "Small Area 1")
        self.assertNotContains(resp, "polygon")
        self.assertNotContains(resp, "New Name")
        self.assertNotContains(resp, "E05000025")

    def test_geometry_delete_confirmation_still_descends(self):
        admin_url = reverse("admin:mapit_geometry_delete", args=(self.geometry.id,))
        resp = self.client.get(admin_url)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "polygon")
        self.assertContains(resp, "subdivision")
