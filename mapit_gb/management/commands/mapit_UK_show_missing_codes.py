from django.core.management.base import NoArgsCommand
from mapit.models import Area, Generation


class Command(NoArgsCommand):
    help = "Prints results of queries to check we aren't missing SNAC and GSS codes"

    def handle_noargs(self, **options):
        current_generation = Generation.objects.current()
        current_areas = Area.objects.filter(
            generation_low__lte=current_generation,
            generation_high__gte=current_generation
        )
        print '{count} areas in current generation ({gen_id})\n'.format(
            count=current_areas.count(),
            gen_id=current_generation.id
        )

        # These types are from
        # http://github.com/alphagov/imminence/blob/26f6c9e5969a9e09bd24d6e2e4ebfe55dba1d997/config/routes.rb#L13
        # except for COI which is used in Frontend:
        # https://github.com/alphagov/frontend/blob/aed183cf3ed6a1e77cf3ec11f7dd6c238a7557cf/lib/location_identifier.rb#L4
        used_area_types = ('EUR', 'CTY', 'DIS', 'LBO', 'LGD', 'MTD', 'UTA', 'COI')
        used_code_types = ('ons', 'gss')  # 'ons' is the SNAC code

        for area_type in used_area_types:
            areas = current_areas.filter(type__code=area_type)
            print '{count} {type} areas in current generation'.format(
                count=areas.count(),
                type=area_type
            )
            for code_type in used_code_types:
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
