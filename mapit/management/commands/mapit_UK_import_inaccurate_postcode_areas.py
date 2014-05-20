from optparse import make_option
import os
import re

from django.core.management.base import LabelCommand, CommandError
from django.core.management import call_command

from mapit.countries.gb import is_valid_postcode
from mapit.models import Area, CodeType, Generation, NameType, Type

class Command(LabelCommand):
    help = 'Import postcode polygons'
    args = '<POSTCODE-KML-DIRECTORY>'

    def handle_label(self, kml_directory, **options):

        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise CommandError, "No new generation to be used for import!"

        if not os.path.isdir(kml_directory):
            raise CommandError, "'%s' is not a directory" % (directory_name,)

        area_type, _ = Type.objects.get_or_create(
            code='IPC',
            defaults={'description': 'Inaccurate postcode area (from Voronoi of Code-Point coords)'})

        name_type, _ = NameType.objects.get_or_create(
            code='uk-pc-name',
            defaults={'description': 'A UK postcode'})

        code_type, _ = CodeType.objects.get_or_create(
            code='uk-pc',
            defaults={'description': 'A UK postcode without whitespace'})

        # In case we're restarting after a failed import, check what
        # the last postcode to be imported into this generation was:
        last_imported = None
        possible_last = Area.objects.filter(type=area_type,
                                            generation_high__gte=new_generation,
                                            generation_low__lte=new_generation).order_by('-name')[:1]
        if len(possible_last) > 0:
            last_imported = possible_last[0].name

        for kml_filename in sorted(os.listdir(kml_directory)):
            m = re.search(r'^(.*)\.kml$', kml_filename)
            if not m:
                continue
            postcode = m.group(1)
            if last_imported is not None and postcode <= last_imported:
                continue
            print "doing postcode:", postcode
            if not is_valid_postcode:
                raise Exception, "Invalid postcode '%s'" % (postcode,)

            full_filename = os.path.join(kml_directory,
                                         kml_filename)

            command_kwargs = {
                'generation_id': new_generation.id,
                'area_type_code': area_type.code,
                'name_type_code': name_type.code,
                'country_code': 'E', # FIXME: many aren't in England...
                'override_name': postcode,
                'override_code': re.sub(r'\s+', '', postcode),
                'name_field': None,
                'code_field': None,
                'code_type': code_type.code,
                'encoding': None,
                'commit': True,
                'new': False,
                'use_code_as_id': False,
                'fix_invalid_polygons': False,
                'preserve': True
                }

            call_command(
                'mapit_import',
                full_filename,
                **command_kwargs
            )
