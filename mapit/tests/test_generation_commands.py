from django.test import TestCase
from django.core.management import call_command, CommandError
from io import StringIO

from ..models import Area, Country, Generation, Type


class GenerationCreateCommandTests(TestCase):
    """Tests for commands that create MapIt generations"""

    def test_already_new(self):
        Generation.objects.create(active=False, description="One inactive generation")
        with self.assertRaisesRegex(CommandError, r'already have an inactive'):
            call_command('mapit_generation_create')

    def test_no_description(self):
        with self.assertRaisesRegex(CommandError, r'must specify a generation description'):
            call_command('mapit_generation_create')

    def test_no_commit(self):
        stdout = StringIO()
        call_command('mapit_generation_create', desc='An inactive generation', stdout=stdout)
        self.assertEqual(
            stdout.getvalue(),
            'Creating generation...\n...not saving, dry run\n'
        )

    def test_creation(self):
        stdout = StringIO()
        call_command('mapit_generation_create', commit=True, desc='An inactive generation', stdout=stdout)
        gen = Generation.objects.first().id
        self.assertEqual(
            stdout.getvalue(),
            'Creating generation...\n...saved: Generation %d (inactive)\n' % gen
        )


class GenerationActivateCommandTests(TestCase):
    """Tests for commands that activate MapIt generations"""

    def test_no_new(self):
        with self.assertRaisesRegex(CommandError, r'do not have an inactive'):
            call_command('mapit_generation_activate')

    def test_no_commit(self):
        g = Generation.objects.create(active=False, description="One inactive generation")
        stdout = StringIO()
        call_command('mapit_generation_activate', stderr=StringIO(), stdout=stdout)
        self.assertEqual(
            stdout.getvalue(),
            'Generation %s (active) - not activated, dry run\n' % g.id
        )

    def test_activation(self):
        g = Generation.objects.create(active=False, description="One inactive generation")
        stdout = StringIO()
        call_command('mapit_generation_activate', commit=True, stderr=StringIO(), stdout=stdout)
        self.assertEqual(
            stdout.getvalue(),
            'Generation %s (active) - activated\n' % g.id
        )


class GenerationDeactivateCommandTests(TestCase):
    """Tests for commands that deactivate MapIt generations"""

    def test_bad_id(self):
        with self.assertRaisesRegex(Generation.DoesNotExist, 'does not exist'):
            call_command('mapit_generation_deactivate', 0)

    def test_inactive(self):
        g = Generation.objects.create(active=False, description="One inactive generation")
        with self.assertRaisesRegex(CommandError, r"wasn't active"):
            call_command('mapit_generation_deactivate', g.id)

    def test_only_active(self):
        g = Generation.objects.create(active=True, description="One active generation")
        with self.assertRaisesRegex(CommandError, r'the only active generation'):
            call_command('mapit_generation_deactivate', g.id)

    def test_no_commit(self):
        Generation.objects.create(active=True, description="One active generation")
        g2 = Generation.objects.create(active=True, description="Two active generation")
        stdout = StringIO()
        call_command(
            'mapit_generation_deactivate',
            g2.id, stderr=StringIO(), stdout=stdout
        )
        self.assertEqual(
            stdout.getvalue(),
            'Generation %s (inactive) - not deactivated, dry run\n' % g2.id
        )

    def test_activation(self):
        g = Generation.objects.create(active=True, description="One active generation")
        stdout = StringIO()
        call_command(
            'mapit_generation_deactivate',
            g.id, force=True, commit=True, stderr=StringIO(), stdout=stdout
        )
        self.assertEqual(
            stdout.getvalue(),
            'Generation %s (inactive) - deactivated\n' % g.id
        )


class GenerationRaiseCommandTests(TestCase):
    """Tests for commands that manipulate MapIt generations"""

    def test_no_generations(self):
        with self.assertRaisesRegex(CommandError, r'no new inactive'):
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
        with self.assertRaisesRegex(CommandError, r'no currently active'):
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
        wales = Country.objects.create(code='W', name='Wales')

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
        sw = Area.objects.create(
            name='Swansea',
            country=wales,
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
        sw = Area.objects.get(pk=sw.id)

        self.assertEqual(ed.generation_high, inactive)
        self.assertEqual(ca.generation_high, current)
        self.assertEqual(sw.generation_high, current)

        call_command(
            'mapit_generation_raise_on_current_areas',
            commit=True,
            country='E',
            country_mode='all-but',
            stderr=StringIO(),
            stdout=stdout,
        )

        ed = Area.objects.get(pk=ed.id)
        ca = Area.objects.get(pk=ca.id)
        sw = Area.objects.get(pk=sw.id)

        self.assertEqual(ed.generation_high, inactive)
        self.assertEqual(ca.generation_high, current)
        self.assertEqual(sw.generation_high, inactive)

    def test_area_type_restriction(self):
        scotland = Country.objects.create(code='S', name='Scotland')

        area_type_wmc = Type.objects.create(
            code='WMC', description='Westminster Constituency'
        )
        area_type_uta = Type.objects.create(
            code='UTA', description='Unitary Authority'
        )
        area_type_yat = Type.objects.create(
            code='YAT', description='Yet Another Area Type'
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
        area_yat = Area.objects.create(
            name='Yet Another Area',
            country=scotland,
            generation_high=current,
            generation_low=current,
            type=area_type_yat
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
        area_yat = Area.objects.get(pk=area_yat.id)

        self.assertEqual(area_wmc.generation_high, inactive)
        self.assertEqual(area_uta.generation_high, current)
        self.assertEqual(area_yat.generation_high, current)

        call_command(
            'mapit_generation_raise_on_current_areas',
            commit=True,
            type='UTA',
            type_mode='all-but',
            stderr=StringIO(),
            stdout=stdout,
        )

        area_wmc = Area.objects.get(pk=area_wmc.id)
        area_uta = Area.objects.get(pk=area_uta.id)
        area_yat = Area.objects.get(pk=area_yat.id)

        self.assertEqual(area_wmc.generation_high, inactive)
        self.assertEqual(area_uta.generation_high, current)
        self.assertEqual(area_yat.generation_high, inactive)


class GenerationDeleteAreasCommandTests(TestCase):
    """Tests for command that removes areas from a MapIt generations"""

    def test_no_active_generations(self):
        Generation.objects.create(active=True, description="One active generation")
        with self.assertRaisesRegex(CommandError, r'no new inactive generation'):
            call_command('mapit_delete_areas_from_new_generation')

    def test_delete_areas(self):
        cur = Generation.objects.create(active=True, description="One active generation")
        new = Generation.objects.create(active=False, description="One inactive generation")
        area_type = Type.objects.create(code='VIL', description='Villages in Trumptonshire')
        area_trumpton = Area.objects.create(
            name='Trumpton', generation_low=cur, generation_high=new, type=area_type)
        area_chigley = Area.objects.create(
            name='Chigley', generation_low=new, generation_high=new, type=area_type)

        call_command(
            'mapit_delete_areas_from_new_generation',
            commit=True,
            stderr=StringIO(),
            stdout=StringIO(),
        )

        # The old areas will still be cached by the ORM, so refetch
        area_trumpton = Area.objects.get(pk=area_trumpton.id)
        self.assertEqual(area_trumpton.generation_low, cur)
        self.assertEqual(area_trumpton.generation_high, cur)
        with self.assertRaisesRegex(Area.DoesNotExist, 'does not exist'):
            area_chigley = Area.objects.get(pk=area_chigley.id)
