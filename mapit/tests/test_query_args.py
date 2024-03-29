# coding=utf-8

import django
from django.db.models import Q
from django.test import TestCase

if django.get_version() < '2.0':
    # Monkeypatch Q() so it sorts the arguments provided,
    # so our tests can compare for equality
    def q__init__(self, *args, **kwargs):
        super(Q, self).__init__(children=list(args) + list(sorted(kwargs.items())))
    Q.__init__ = q__init__

from mapit.models import Generation
from mapit.views.areas import query_args


class FakeRequest(object):
    def __init__(self, params):
        self.GET = params


class QueryArgsTest(TestCase):

    def setUp(self):
        self.older_generation = Generation.objects.create(
            active=False,
            description="Older test generation",
        )
        self.old_generation = Generation.objects.create(
            active=False,
            description="Old test generation",
        )
        self.active_generation = Generation.objects.create(
            active=True,
            description="Test generation",
        )

    def test_no_type(self):
        q = query_args(FakeRequest({}), 'json', None)
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            )
        )

    def test_one_type_in_query(self):
        q = query_args(FakeRequest({'type': 'WMC'}), 'json', None)
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(type__code='WMC'))
        )

    def test_two_types_in_query(self):
        q = query_args(FakeRequest({'type': 'WMC,EUR'}), 'json', None)
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(type__code__in=['WMC', 'EUR']))
        )

    def test_one_type_in_params(self):
        q = query_args(FakeRequest({}), 'json', 'WMC')
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(type__code='WMC'))
        )

    def test_two_types_in_params(self):
        q = query_args(FakeRequest({}), 'json', 'WMC,EUR')
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(type__code__in=['WMC', 'EUR']))
        )

    def test_generation_specified(self):
        q = query_args(
            FakeRequest({'generation': self.old_generation.id}),
            'json',
            None)
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.old_generation.id,
                generation_low__lte=self.old_generation.id,
            )
        )

    def test_min_generation_specified(self):
        q = query_args(
            FakeRequest({'min_generation': self.old_generation.id}),
            'json',
            None)
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.old_generation.id,
                generation_low__lte=self.active_generation.id,
            )
        )

    def test_one_country_in_query(self):
        q = query_args(FakeRequest({'country': 'DE'}), 'json', None)
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(country__code='DE') | Q(countries__code='DE'))
        )

    def test_two_countries_in_query(self):
        q = query_args(FakeRequest({'country': 'DE,FR'}), 'json', None)
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(country__code__in=['DE', 'FR']) | Q(countries__code__in=['DE', 'FR']))
        )

    def test_generation_manager_query_args(self):
        q = Generation.objects.query_args(
            FakeRequest({'generation': self.old_generation.id}),
            'json')
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.old_generation.id,
                generation_low__lte=self.old_generation.id,
            )
        )

        q = Generation.objects.query_args(
            FakeRequest({'min_generation': self.old_generation.id}),
            'json')
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.old_generation.id,
                generation_low__lte=self.active_generation.id,
            )
        )

        q = Generation.objects.query_args(
            FakeRequest({'max_generation': self.old_generation.id}),
            'json')
        self.assertEqual(
            q,
            Q(
                generation_high__lte=self.old_generation.id,
                generation_low__lte=self.active_generation.id,
            )
        )

        q = Generation.objects.query_args(
            FakeRequest({
                'max_generation': self.old_generation.id, 'min_generation': self.older_generation.id
            }),
            'json')
        self.assertEqual(
            q,
            Q(
                generation_high__gte=self.older_generation.id,
                generation_high__lte=self.old_generation.id,
                generation_low__lte=self.active_generation.id,
            )
        )
