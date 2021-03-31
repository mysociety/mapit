# coding=utf8

from __future__ import print_function
from django.core.management.base import BaseCommand
from django.contrib.gis.db.models import Union
from mapit.models import Area, Generation, Type, Country, NameType, CodeType


class Command(BaseCommand):
    help = "Sort out boundaries for council changes"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true')

    def handle(self, *args, **options):
        self.commit = options['commit']
        self.g = Generation.objects.current()
        self.gn = Generation.objects.new()
        self.name_type = NameType.objects.get(code='O')
        self.code_type = CodeType.objects.get(code='gss')
        self.country = Country.objects.get(code='E')

        self.raise_generation_on_everything_else()

        self.areas = Area.objects.filter(generation_low_id__lte=self.g, generation_high_id__gte=self.g)

        self.get_existing()
        self.create_new_unitaries()

    def _exclude_councils_and_wards(self, qs, names, type_p, type_c):
        areas = Area.objects.filter(type__code=type_p, name__in=names, generation_high=self.g)
        wards = Area.objects.filter(type__code=type_c, parent_area__in=areas, generation_high=self.g)
        qs = qs.exclude(id__in=areas).exclude(id__in=wards)
        return qs

    def raise_generation_on_everything_else(self):
        qs = Area.objects.filter(generation_high=self.g)
        print('%d areas in database' % qs.count())
        qs = self._exclude_councils_and_wards(qs, (self.county,), 'CTY', 'CED')
        qs = self._exclude_councils_and_wards(qs, self.districts, 'DIS', 'DIW')

        if self.commit:
            print('Raising gen high on %d areas' % qs.count())
            updated = qs.update(generation_high=self.gn)
            print('Raised gen high on %d areas' % updated)
        else:
            print('Would raise gen high on %d areas' % qs.count())

    def get_existing(self):
        self.existing_cty = Area.objects.get(type__code='CTY', name=self.county)

    def _create(self, name, typ, area, gss=None):
        if isinstance(area, Area):
            assert(area.polygons.count() == 1)
            geom = area.polygons.get().polygon
        else:
            geom = self._union(area)
        m = Area(
            name=name, type=Type.objects.get(code=typ), country=self.country,
            generation_low=self.gn, generation_high=self.gn,
        )
        if self.commit:
            m.save()
            m.names.update_or_create(type=self.name_type, defaults={'name': name})
            if gss:
                m.codes.update_or_create(type=self.code_type, defaults={'code': gss})
            m.polygons.create(polygon=geom)
        else:
            print('Would create', name, typ)

    def _union(self, qs):
        qs = qs.aggregate(Union('polygons__polygon'))
        area = qs['polygons__polygon__union']
        return area

    def create_new_unitaries(self):
        """New areas are the existing county electoral divisions"""
        for new_uta in self.new_utas:
            if new_uta[2]:
                area = Area.objects.filter(type__code='DIS', name__in=new_uta[2], generation_high=self.g)
            else:
                area = self.existing_cty
            self._create(new_uta[0], 'UTA', area, new_uta[1])
        for area in self.areas.filter(type__code='CED', parent_area=self.existing_cty):
            self._create(area.name, 'UTW', area)
