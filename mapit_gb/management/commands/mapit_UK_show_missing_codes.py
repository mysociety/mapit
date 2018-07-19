from django.core.management.base import BaseCommand
from mapit.models import Area, Generation
import argparse


class Command(BaseCommand):
    help = "Prints results of queries to check we aren't missing SNAC and GSS codes"

    def add_arguments(self, parser):
        parser.add_argument("--code_types",
            dest="code_types",
            help="The list of code types to search for",
            default="ons,gss,govuk_slug"
        )

        parser.add_argument("--area_types",
            dest="area_types",
            help="The list of area types to search for",
            # These types are from
            # http://github.com/alphagov/imminence/blob/26f6c9e5969a9e09bd24d6e2e4ebfe55dba1d997/config/routes.rb#L13
            # except for COI which is used in Frontend:
            # https://github.com/alphagov/frontend/blob/aed183cf3ed6a1e77cf3ec11f7dd6c238a7557cf/lib/location_identifier.rb#L4
            default="EUR,CTY,DIS,LBO,LGD,MTD,UTA,COI",
        )

    def handle(self, *args, **options):
        current_generation = Generation.objects.current()
        current_areas = Area.objects.filter(
            generation_low__lte=current_generation,
            generation_high__gte=current_generation
        )
        print '{count} areas in current generation ({gen_id})\n'.format(
            count=current_areas.count(),
            gen_id=current_generation.id
        )

        used_area_types = options['area_types'].split(',')
        used_code_types = options['code_types'].split(',')

        print 'Checking {area_types} for missing {code_types}'.format(
            area_types=used_area_types,
            code_types=used_code_types
        )

        for area_type in used_area_types:
            areas = current_areas.filter(type__code=area_type)
            print '{count} {type} areas in current generation'.format(
                count=areas.count(),
                type=area_type
            )
            for code_type in used_code_types:
                if self.is_code_type_not_required_for_area_type(code_type, area_type):
                    continue

                areas_without_codes = areas.exclude(codes__type__code=code_type)
                if areas_without_codes.count() > 0:
                    print '  {count} {type} areas have no {code_type} code:'.format(
                        count=areas_without_codes.count(),
                        type=area_type,
                        code_type=code_type
                    )
                    for area in areas_without_codes:
                        print '    {name} {id} (gen {gen_low}-{gen_high}) {country}'.format(
                            name=area.name,
                            id=area.id,
                            gen_low=area.generation_low_id,
                            gen_high=area.generation_high_id,
                            country=area.country
                        )

    def is_code_type_not_required_for_area_type(self, code_type, area_type):
        return (code_type == "govuk_slug" and area_type == "EUR")
