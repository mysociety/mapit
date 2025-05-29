# This script is used to import Northern Ireland areas into MaPit
#
# XXX This is incomplete, it needs to know which things have had boundary changes
# like import_boundary_line does. Hopefully just using new GSS codes by the time
# NI has any boundary changes.

import csv
import re
import os.path
from django.core.management.base import BaseCommand
from mapit.models import Area, Generation, Country, Type, CodeType, NameType


class Command(BaseCommand):
    help = 'Creates/updates Northern Ireland areas'

    def handle(self, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        country = Country.objects.get(code='N')
        if not new_generation:
            raise Exception("No new generation to be used for import!")

        code_type = CodeType.objects.get(code='gss')
        name_type = NameType.objects.get(code='S')

        euro_area, created = Area.objects.get_or_create(
            country=country, type=Type.objects.get(code='EUR'),
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            defaults={'generation_low': new_generation, 'generation_high': new_generation}
        )
        euro_area.generation_high = new_generation
        euro_area.save()
        euro_area.names.get_or_create(type=name_type, name='Northern Ireland')

        # Read in ward name -> electoral area name/area
        ni_eas = csv.reader(open(os.path.dirname(__file__) + '/../../data/ni-electoral-areas.csv'))
        next(ni_eas)
        ward_to_electoral_area = {}
        e = {}
        last_district = None
        last_electoral_area = None
        for district, electoral_area, ward, dummy in ni_eas:
            if not district:
                district = last_district
            if not electoral_area:
                electoral_area = last_electoral_area
            last_district = district
            last_electoral_area = electoral_area
            if electoral_area not in e:
                ea = Area.objects.get_or_create_with_name(
                    country=country, type=Type.objects.get(code='LGE'), name_type='M', name=electoral_area,
                )
                e[electoral_area] = ea
            ward_to_electoral_area.setdefault(district, {})[ward] = e[electoral_area]

        # Read in new ONS code to names
        snac = csv.reader(open(os.path.dirname(__file__) + '/../../data/snac-2009-ni-cons2ward.csv'))
        next(snac)
        code_to_area = {}
        for parl_code, parl_name, ward_code, ward_name, district_code, district_name in snac:
            if district_name not in ward_to_electoral_area:
                raise Exception("District %s is missing" % district_name)
            if ward_name not in ward_to_electoral_area[district_name]:
                raise Exception("Ward %s, district %s is missing" % (ward_name, district_name))

            ward_code = ward_code.replace(' ', '')

            if district_code not in code_to_area:
                district_area = Area.objects.get_or_create_with_code(
                    country=country, type=Type.objects.get(code='LGD'), code_type='ons', code=district_code,
                )
                district_area.names.get_or_create(type=name_type, name=district_name)
                code_to_area[district_code] = district_area

            if ward_code not in code_to_area:
                ward_area = Area.objects.get_or_create_with_code(
                    country=country, type=Type.objects.get(code='LGW'), code_type='ons', code=ward_code
                )
                ward_area.names.get_or_create(type=name_type, name=ward_name)
                ward_area.parent_area = ward_to_electoral_area[district_name][ward_name]
                ward_area.save()
                ward_area.parent_area.parent_area = code_to_area[district_code]
                ward_area.parent_area.save()
                code_to_area[ward_code] = ward_area

            if ward_code == '95S24':
                continue  # Derryaghy

            if parl_code not in code_to_area:
                parl_area = Area.objects.get_or_create_with_code(
                    country=country, type=Type.objects.get(code='WMC'), code_type='ons', code=parl_code,
                )
                parl_area.names.get_or_create(type=name_type, name=parl_name)
                new_code = re.sub('^7', 'N060000', parl_code)
                parl_area.codes.get_or_create(type=code_type, code=new_code)
                code_to_area[parl_code] = parl_area

            if 'NIE' + parl_code not in code_to_area:
                nia_area = Area.objects.get_or_create_with_name(
                    country=country, type=Type.objects.get(code='NIE'), name_type='S', name=parl_name,
                )
                code_to_area['NIE' + parl_code] = nia_area
