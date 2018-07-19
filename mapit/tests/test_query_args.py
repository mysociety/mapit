# coding=utf-8

from django.db.models import Q
from django.test import TestCase

from mapit.models import Generation
from mapit.views.areas import query_args


class FakeRequest(object):
    def __init__(self, params):
        self.GET = params


class QueryArgsTest(TestCase):

    def setUp(self):
        self.old_generation = Generation.objects.create(
            active=False,
            description="Old test generation",
        )
        self.active_generation = Generation.objects.create(
            active=True,
            description="Test generation",
        )

    def q_equality(self, act, exp):
        self.assertEqual(str(act), str(exp))

    def test_no_type(self):
        q = query_args(FakeRequest({}), 'json', None)
        self.q_equality(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            )
        )

    def test_one_type_in_query(self):
        q = query_args(FakeRequest({'type': 'WMC'}), 'json', None)
        self.q_equality(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(type__code='WMC'))
        )

    def test_two_types_in_query(self):
        q = query_args(FakeRequest({'type': 'WMC,EUR'}), 'json', None)
        self.q_equality(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(type__code__in=['WMC', 'EUR']))
        )

    def test_one_type_in_params(self):
        q = query_args(FakeRequest({}), 'json', 'WMC')
        self.q_equality(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(type__code='WMC'))
        )

    def test_two_types_in_params(self):
        q = query_args(FakeRequest({}), 'json', 'WMC,EUR')
        self.q_equality(
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
        self.q_equality(
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
        self.q_equality(
            q,
            Q(
                generation_high__gte=self.old_generation.id,
                generation_low__lte=self.active_generation.id,
            )
        )

    def test_one_country_in_query(self):
        q = query_args(FakeRequest({'country': 'DE'}), 'json', None)
        self.q_equality(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(country__code='DE') | Q(countries__code='DE'))
        )

    def test_two_countries_in_query(self):
        q = query_args(FakeRequest({'country': 'DE,FR'}), 'json', None)
        self.q_equality(
            q,
            Q(
                generation_high__gte=self.active_generation.id,
                generation_low__lte=self.active_generation.id,
            ) & (Q() | Q(country__code__in=['DE', 'FR']) | Q(countries__code__in=['DE', 'FR']))
        )
