# If you've created a new generation for importing a new data set into
# a MapIt database with lots of existing active areas, you need to
# raise generation_high on all of those areas to be the ID of the new
# generation, or when you activate that new generation, none of the
# existing areas will be shown in results. This command provides a
# safe way of raising the generation_high of all active areas to the
# ID of the new inactive generation.

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from mapit.models import Area, Generation, Type, Country


def lookup_model_by_code(option_name, model_class, code):
    known = model_class.objects.order_by('code'). \
        values_list('code', flat=True)
    try:
        return model_class.objects.get(code=code)
    except model_class.DoesNotExist:
        raise CommandError(
            'The {option_name} {code} is not known - did you mean '
            'one of: {known}'.format(
                code=code,
                known=', '.join(known),
                option_name=option_name
            )
        )


def check_option(option_name, options, model_class):
    '''Get model instances from an option specifying code field values'''
    supplied = options[option_name]
    if not supplied:
        return []
    if type(supplied) != list:
        supplied = [supplied]
    return [lookup_model_by_code(option_name, model_class, code) for code in supplied]


class Command(BaseCommand):
    help = "Raise generation_high on active areas to the new generation's ID"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')
        parser.add_argument('--country', nargs="*", help='Country codes used as specified by --country-mode')
        parser.add_argument('--type', nargs="*", help='Area type codes used as specified by --type-mode.')
        parser.add_argument(
            '--type-mode', choices=['all-but', 'nothing-but'], default="nothing-but",
            help='Determines how the given types are used to select areas to raise the generation of.'
        )
        parser.add_argument(
            '--country-mode', choices=['all-but', 'nothing-but'], default="nothing-but",
            help='Determines how the given countries are used to select areas to raise the generation of.'
        )

    def handle(self, **options):
        area_types = check_option('type', options, Type)
        countries = check_option('country', options, Country)
        include_types = options['type_mode'] == 'nothing-but'
        include_countries = options['country_mode'] == 'nothing-but'

        new_generation = Generation.objects.new()
        if not new_generation:
            raise CommandError("There is no new inactive generation")
        current_generation = Generation.objects.current()
        if not current_generation:
            raise CommandError("There is no currently active generation")

        qs = Area.objects.filter(generation_high=current_generation)

        if area_types:
            area_type_filter = Q(type__in=area_types)
            qs = qs.filter(area_type_filter if include_types else ~area_type_filter)

        if countries:
            country_filter = Q(country__in=countries)
            qs = qs.filter(country_filter if include_countries else ~country_filter)

        if options['commit']:
            updated = qs.update(generation_high=new_generation)
            message = "Successfully updated generation_high on {0} areas"
            self.stdout.write(message.format(updated))
        else:
            self.stdout.write("Not updating since --commit wasn't specified")
            self.stdout.write(
                "But this would have set generation_high to {0} on:".format(
                    new_generation
                )
            )
            for a in qs:
                self.stdout.write("  " + str(a))
