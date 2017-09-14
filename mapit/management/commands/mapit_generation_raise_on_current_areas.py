# If you've created a new generation for importing a new data set into
# a MapIt database with lots of existing active areas, you need to
# raise generation_high on all of those areas to be the ID of the new
# generation, or when you activate that new generation, none of the
# existing areas will be shown in results. This command provides a
# safe way of raising the generation_high of all active areas to the
# ID of the new inactive generation.

from django.core.management.base import BaseCommand, CommandError

from mapit.models import Area, Generation, Type, Country


def check_option(option_name, options, model_class):
    '''Get a model instance from an option specifying its code field'''

    supplied = options[option_name]
    if not supplied:
        return None
    known = model_class.objects.order_by('code'). \
        values_list('code', flat=True)
    try:
        return model_class.objects.get(code=supplied)
    except model_class.DoesNotExist:
        raise CommandError(
            'The {option_name} {supplied} is not known - did you mean '
            'one of: {known}'.format(
                supplied=supplied,
                known=', '.join(known),
                option_name=option_name
            )
        )


class Command(BaseCommand):
    help = "Raise generation_high on active areas to the new generation's ID"

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')
        parser.add_argument('--country', help='Only raise the generation on areas with this country code')
        parser.add_argument('--type', help='Only raise the generation on areas with this area type code')

    def handle(self, **options):
        area_type = check_option('type', options, Type)
        country = check_option('country', options, Country)

        new_generation = Generation.objects.new()
        if not new_generation:
            raise CommandError("There is no new inactive generation")
        current_generation = Generation.objects.current()
        if not current_generation:
            raise CommandError("There is no currently active generation")

        qs = Area.objects.filter(generation_high=current_generation)
        if area_type:
            qs = qs.filter(type=area_type)
        if country:
            qs = qs.filter(country=country)

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
