# coding=UTF-8
# This script is used to add GSS codes to NI areas that don't have them, having
# been imported prior to OSNI releases.

import csv
import os.path

from django.core.management.base import BaseCommand
from mapit.models import Area, Generation, Country, CodeType
from django.utils import six


class Command(BaseCommand):
    help = 'Uses fixtures to find NI areas and add any missing GSS codes to them'

    def handle(self, **options):
        try:
            self.latest_generation = Generation.objects.order_by('-id')[0]
        except IndexError:
            raise Exception("No generation to be used for import!")
        self.country = Country.objects.get(code='N')

        self.gss_code_type = CodeType.objects.get(code='gss')

        self.add_gss_code_to_eur_area()
        council_areas = self.fetch_council_areas_hierarchy()
        self.update_lgds(council_areas)

    def add_gss_code_to_eur_area(self):
        euro_area, code_created = self.fetch_and_update_area(
            Area.objects, 'EUR', 'Northern Ireland', 'N07000001'
        )
        if euro_area:
            self.report_result('EUR "Northern Ireland" - GSS code "N07000001"', code_created)
        else:
            self.stdout.write('WARNING: No EUR area with name "Northern Ireland" to add GSS code "N07000001" to')

    def update_lgds(self, districts):
        for district in districts:
            district_name, district_gss_code = district
            lgd, code_created = self.fetch_and_update_area(
                Area.objects, 'LGD', district_name, district_gss_code
            )
            if lgd:
                self.report_result(
                    'LGD "%s" - GSS code "%s" ' % (district_name, district_gss_code),
                    code_created)
                self.update_lges_for_lgd(districts[district], lgd)
            else:
                self.stdout.write('WARNING: No LGD with name "%s" to add GSS "%s" to' % (
                    district_name, district_gss_code))

    def update_lges_for_lgd(self, electoral_areas, lgd):
        for electoral_area in electoral_areas:
            electoral_area_name, electoral_area_gss_code = electoral_area
            lge, code_created = self.fetch_and_update_area(
                lgd.children, 'LGE', electoral_area_name, electoral_area_gss_code
            )
            if lge:
                self.report_result(
                    ('LGE "%s" (child of LGD "%s") - GSS code "%s" ')
                    % (electoral_area_name, lgd.name, electoral_area_gss_code),
                    code_created)
                self.update_lgws_for_lge(electoral_areas[electoral_area], lgd, lge)
            else:
                self.stdout.write(('WARNING: No LGE with name "%s" as child of LGD "%s" to '
                                   'add GSS "%s" to') % (electoral_area_name, lgd.name, electoral_area_gss_code))

    def update_lgws_for_lge(self, wards, lgd, lge):
        for ward in wards:
            ward_name, ward_gss_code = ward
            lgw, code_created = self.fetch_and_update_area(
                lge.children, 'LGW', ward_name, ward_gss_code
            )
            if lgw:
                self.report_result(
                    ('LGW "%s" (child of LGE "%s" and LGD "%s") '
                     '- GSS code "%s" ') % (ward_name, lge.name, lgd.name, ward_gss_code),
                    code_created)
            else:
                self.stdout.write(('WARNING: No LGW with name "%s" as child of LGE "%s" and'
                                   ' LGD "%s" to add GSS "%s" to') % (ward_name, lge.name, lgd.name, ward_gss_code))

    def fetch_and_update_area(self, area_source, area_type, area_name, area_gss_code):
        area_name = area_name.replace('St. ', 'St ')
        try:
            area = area_source.get(
                country=self.country, type__code=area_type,
                name__iexact=area_name,
                generation_low__lte=self.latest_generation,
                generation_high__gte=self.latest_generation
            )
        except Area.DoesNotExist:
            try:
                area = area_source.get(
                    country=self.country, type__code=area_type,
                    name__istartswith=area_name,
                    generation_low__lte=self.latest_generation,
                    generation_high__gte=self.latest_generation
                )
            except Area.DoesNotExist:
                return None, False
        else:
            _code, code_created = area.codes.get_or_create(type=self.gss_code_type, code=area_gss_code)
            return area, code_created

    def report_result(self, message, code_created):
        self.stdout.write(message, ending=' ')
        if code_created:
            self.stdout.write("added")
        else:
            self.stdout.write("already present")

    def fetch_council_areas_hierarchy(self):
        # Read in district + gss -> electoral area + gss -> ward +gss
        ni_areas = csv.reader(open(os.path.dirname(__file__) + '/../../data/ni-electoral-areas-2015.csv'))
        next(ni_areas)  # comment line
        next(ni_areas)  # header row

        council_areas = {}
        current_district = None
        current_electoral_area = None

        for district, district_gss_code, electoral_area, electoral_area_gss_code, ward, ward_gss_code in ni_areas:
            if not district:
                district, district_gss_code = current_district
            if not electoral_area:
                electoral_area, electoral_area_gss_code = current_electoral_area
            current_district = (self.format_name(district), district_gss_code)
            current_electoral_area = (self.format_name(electoral_area), electoral_area_gss_code)

            if current_district not in council_areas:
                council_areas[current_district] = {}

            if current_electoral_area not in council_areas[current_district]:
                council_areas[current_district][current_electoral_area] = []

            council_areas[current_district][current_electoral_area].append((self.format_name(ward), ward_gss_code))

        return council_areas

    def format_name(self, name):
        if not isinstance(name, six.text_type):
            name = name.decode('utf-8 ')
        return name
