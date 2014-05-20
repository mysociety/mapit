from optparse import make_option
import os
import re

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import NoArgsCommand, CommandError
from django.core.management import call_command

from mapit.countries.gb import is_valid_postcode
from mapit.models import (Area, CodeType, Country, Geometry, Generation,
    NameType, Type)

from mapit.management.command_utils import save_polygons

class Command(NoArgsCommand):
    help = 'Import postcode polygons'

    option_list = NoArgsCommand.option_list + (
        make_option('--commit', action='store_true', dest='commit', help='Actually update the database'),
    )

    def handle(self, **options):

        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise CommandError, "No new generation to be used for import!"

        single_postcode_type = Type.objects.get(code='IPC')

        district_postcode_type, _ = Type.objects.get_or_create(
            code='APD',
            defaults={'description': 'Approximate Postcode District'})

        sector_postcode_type, _ = Type.objects.get_or_create(
            code='APS',
            defaults={'description': 'Approximate Postcode Sector'})

        # The Wikipedia page suggests that there's some inconsistency
        # in the descriptive terms for regions aggregated out of
        # postcodes, but I'm using the terminology they suggest:
        #    A postcode sector is all but the last two letters,
        #      e.g. SW2 1
        #      e.g. EC1V 7
        #    A postcode district is all but the last three letters,
        #      e.g. SW2
        #      e.g. EC1V

        districts = set()
        sectors = set()

        for a in Area.objects.filter(type=single_postcode_type,
                                     generation_low__lte=new_generation,
                                     generation_high__gte=new_generation):
            sector = re.sub('..$', '', a.name).strip()
            # Don't strip the district - we need the space to be in
            # the prefix or else we'll group 'CB11' in 'CB1'
            district = re.sub('...$', '', a.name)
            sectors.add(sector)
            districts.add(district)

        # FIXME: instead, find the distinct country in all the areas
        country = Country.objects.get(code='E')

        for prefixes, area_type in [(districts, district_postcode_type),
                                    (sectors, sector_postcode_type)]:
            for prefix in prefixes:
                geometries = Geometry.objects.filter(area__type__code='IPC',
                                                     area__name__startswith=prefix,
                                                     area__generation_low__lte=new_generation,
                                                     area__generation_high__gte=new_generation)
                mp = geometries.unionagg()

                m, _ = Area.objects.get_or_create(
                    name = prefix.strip(),
                    type = area_type,
                    country = country,
                    parent_area = None,
                    generation_low = new_generation,
                    generation_high = new_generation,
                )

                poly = [ GEOSGeometry(mp).ogr ]
                if options['commit']:
                    m.save()
                    save_polygons({'ignored': (m, poly) })
