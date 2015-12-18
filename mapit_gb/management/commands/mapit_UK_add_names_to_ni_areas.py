# coding=UTF-8
# This script is used to add names to NI areas where the names of the areas
# don't include the names from the legislation derived fixture data.

import csv
import os.path

from django.core.management.base import NoArgsCommand
from mapit.models import Area, Generation, Country, NameType
from django.utils import six


class Command(NoArgsCommand):
    help = 'Uses fixtures to find NI areas and add any missing names to them'

    def handle_noargs(self, **options):
        self.current_generation = Generation.objects.current()
        self.new_generation = Generation.objects.new()
        self.country = Country.objects.get(code='N')
        if not self.new_generation:
            raise Exception("No new generation to be used for import!")

        self.name_type = NameType.objects.get(code='M')

        council_areas = self.fetch_council_areas()
        self.update_area_names(council_areas)

    def update_area_names(self, council_areas):
        for gss_code in council_areas:
            name, area_type = council_areas[gss_code]
            area, name_created = self.fetch_and_update_area(area_type, name, gss_code)
            if area:
                self.report_result('%s "%s" - name "%s" ' % (area_type, gss_code, name), name_created)
            else:
                print 'WARNING: No %s with GSS code "%s" to add name "%s" to' % (area_type, gss_code, name)

    def fetch_and_update_area(self, area_type, area_name, area_gss_code):
        try:
            area = Area.objects.get(
                country=self.country, type__code=area_type,
                codes__type__code='gss', codes__code=area_gss_code,
                generation_low__lte=self.current_generation,
                generation_high__gte=self.current_generation
            )
            area.generation_high = self.new_generation
            area.save()
            _name, name_created = area.names.get_or_create(name=area_name, defaults={'type': self.name_type})
            return area, name_created
        except Area.DoesNotExist:
            return None, False

    def report_result(self, message, name_created):
        print message,
        if name_created:
            print "added"
        else:
            print "already present"

    def fetch_council_areas(self):
        # Read in district + gss -> electoral area + gss -> ward +gss
        ni_areas = csv.reader(open(os.path.dirname(__file__) + '/../../data/ni-electoral-areas-2015.csv'))
        next(ni_areas)  # comment line
        next(ni_areas)  # header row

        council_areas = {}

        for district, district_gss_code, electoral_area, electoral_area_gss_code, ward, ward_gss_code in ni_areas:
            if district:
                council_areas[district_gss_code] = (self.format_name(district), 'LGD')

            if electoral_area:
                council_areas[electoral_area_gss_code] = (self.format_name(electoral_area), 'LGE')

            council_areas[ward_gss_code] = (self.format_name(ward), 'LGW')

        return council_areas

    def format_name(self, name):
        if not isinstance(name, six.text_type):
            name = name.decode('utf-8 ')
        return name
