from django.test import TestCase
from django.core.management import call_command, CommandError
from django.utils.six import StringIO, assertRaisesRegex

from ..models import Area, Country, Generation, Type


class GenerationCommandTests(TestCase):
    """Tests for commands that manipulate MapIt generations"""

    def test_no_generations(self):
        with assertRaisesRegex(self, CommandError, r'no new inactive'):
            call_command(
                'mapit_generation_raise_on_current_areas',
                commit=True,
                stderr=StringIO(),
                stdout=StringIO()
            )

    def test_no_active_generations(self):
        Generation.objects.create(
            active=False,
            description="One inactive generation",
        )
        with assertRaisesRegex(self, CommandError, r'no currently active'):
            call_command(
                'mapit_generation_raise_on_current_areas',
                commit=True,
                stderr=StringIO(),
                stdout=StringIO()
            )

    def test_should_raise_generation_of_one_area(self):
        area_type = Type.objects.create(
            code='VIL',
            description='Villages in Trumptonshire'
        )

        first = Generation.objects.create(
            active=True,
            description="First active generation",
        )
        current = Generation.objects.create(
            active=True,
            description="Current active generation",
        )
        inactive = Generation.objects.create(
            active=False,
            description="New inactive generation",
        )
        area_trumpton = Area.objects.create(
            name='Trumpton',
            generation_low=first,
            generation_high=current,
            type=area_type,
        )
        area_chigley = Area.objects.create(
            name='Chigley',
            generation_low=first,
            generation_high=first,
            type=area_type,
        )

        stdout = StringIO()
        call_command(
            'mapit_generation_raise_on_current_areas',
            commit=True,
            stderr=StringIO(),
            stdout=stdout,
        )

        # The old areas will still be cached by the ORM, so refetch them:
        area_trumpton = Area.objects.get(pk=area_trumpton.id)
        area_chigley = Area.objects.get(pk=area_chigley.id)

        self.assertEqual(
            stdout.getvalue(),
            'Successfully updated generation_high on 1 areas\n'
        )

        self.assertEqual(area_trumpton.generation_low, first)
        self.assertEqual(area_trumpton.generation_high, inactive)
        self.assertEqual(area_chigley.generation_low, first)
        self.assertEqual(area_chigley.generation_high, first)

    def test_country_restriction(self):
        scotland = Country.objects.create(code='S', name='Scotland')
        england = Country.objects.create(code='E', name='England')

        area_type = Type.objects.create(
            code='WMC', description='Westminster Constituency'
        )

        current = Generation.objects.create(
            active=True,
            description="Current active generation",
        )
        inactive = Generation.objects.create(
            active=False,
            description="New inactive generation",
        )

        ed = Area.objects.create(
            name='Edinburgh East',
            country=scotland,
            generation_high=current,
            generation_low=current,
            type=area_type
        )
        ca = Area.objects.create(
            name='South Cambridgeshire',
            country=england,
            generation_high=current,
            generation_low=current,
            type=area_type
        )

        stdout = StringIO()

        call_command(
            'mapit_generation_raise_on_current_areas',
            commit=True,
            country='S',
            stderr=StringIO(),
            stdout=stdout,
        )

        ed = Area.objects.get(pk=ed.id)
        ca = Area.objects.get(pk=ca.id)

        self.assertEqual(ed.generation_high, inactive)
        self.assertEqual(ca.generation_high, current)

    def test_area_type_restriction(self):
        scotland = Country.objects.create(code='S', name='Scotland')

        area_type_wmc = Type.objects.create(
            code='WMC', description='Westminster Constituency'
        )
        area_type_uta = Type.objects.create(
            code='UTA', description='Unitary Authority'
        )

        current = Generation.objects.create(
            active=True,
            description="Current active generation",
        )
        inactive = Generation.objects.create(
            active=False,
            description="New inactive generation",
        )

        area_wmc = Area.objects.create(
            name='Edinburgh East',
            country=scotland,
            generation_high=current,
            generation_low=current,
            type=area_type_wmc
        )
        area_uta = Area.objects.create(
            name='City of Edinburgh Council',
            country=scotland,
            generation_high=current,
            generation_low=current,
            type=area_type_uta
        )

        stdout = StringIO()

        call_command(
            'mapit_generation_raise_on_current_areas',
            commit=True,
            type='WMC',
            stderr=StringIO(),
            stdout=stdout,
        )

        area_wmc = Area.objects.get(pk=area_wmc.id)
        area_uta = Area.objects.get(pk=area_uta.id)

        self.assertEqual(area_wmc.generation_high, inactive)
        self.assertEqual(area_uta.generation_high, current)
