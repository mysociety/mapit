# coding=utf-8

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

    def test_no_type(self):
        args = query_args(FakeRequest({}), 'json', None)
        self.assertEqual(
            args,
            {
                'generation_high__gte': self.active_generation.id,
                'generation_low__lte': self.active_generation.id,
            }
        )

    def test_one_type_in_query(self):
        args = query_args(FakeRequest({'type': 'WMC'}), 'json', None)
        self.assertEqual(
            args,
            {
                'generation_high__gte': self.active_generation.id,
                'generation_low__lte': self.active_generation.id,
                'type__code': 'WMC',
            }
        )

    def test_two_types_in_query(self):
        args = query_args(FakeRequest({'type': 'WMC,EUR'}), 'json', None)
        self.assertEqual(
            args,
            {
                'generation_high__gte': self.active_generation.id,
                'generation_low__lte': self.active_generation.id,
                'type__code__in': ['WMC', 'EUR'],
            }
        )

    def test_one_type_in_params(self):
        args = query_args(FakeRequest({}), 'json', 'WMC')
        self.assertEqual(
            args,
            {
                'generation_high__gte': self.active_generation.id,
                'generation_low__lte': self.active_generation.id,
                'type__code': 'WMC',
            }
        )

    def test_two_types_in_params(self):
        args = query_args(FakeRequest({}), 'json', 'WMC,EUR')
        self.assertEqual(
            args,
            {
                'generation_high__gte': self.active_generation.id,
                'generation_low__lte': self.active_generation.id,
                'type__code__in': ['WMC', 'EUR'],
            }
        )

    def test_generation_specified(self):
        args = query_args(
            FakeRequest({'generation': self.old_generation.id}),
            'json',
            None)
        self.assertEqual(
            args,
            {
                'generation_high__gte': self.old_generation.id,
                'generation_low__lte': self.old_generation.id,
            }
        )

    def test_min_generation_specified(self):
        args = query_args(
            FakeRequest({'min_generation': self.old_generation.id}),
            'json',
            None)
        self.assertEqual(
            args,
            {
                'generation_high__gte': self.old_generation.id,
                'generation_low__lte': self.active_generation.id,
            }
        )
