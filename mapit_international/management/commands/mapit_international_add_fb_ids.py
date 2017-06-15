import re

from django.core.management.base import BaseCommand
from django.db.models import Prefetch

from mapit.models import Area, Code, CodeType


def get_code(area, code_type_code):
    for code in area.codes.all():
        if code.type.code == code_type_code:
            return code.code
    raise Exception(
        "No code of type {0} found for area {1} with codes: {2}".format(
            code_type_code, area.id, area.codes.all()))


class Command(BaseCommand):

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('GENERATION', type=int)

    def handle(self, **options):
        fb_code_type, _ = CodeType.objects.get_or_create(
            code='fb',
            defaults={'description': "Area ID we're using in FB data"})
        for area in Area.objects.filter(
                country__code='FR',
                generation_low__lte=options['GENERATION'],
                generation_high__gte=options['GENERATION']
        ).prefetch_related(
            Prefetch('codes', Code.objects.select_related('type'))):
            type_code = area.type.code
            new_fb_code = None
            if type_code == 'FRDEP':
                code_from_shapefile = get_code(area, 'insee-dep')
                m = re.search(r'^([0-9]+)([A-Z]?)$', code_from_shapefile)
                department = int(m.group(1))
                suffix = m.group(2)
                new_fb_code = 'insee-dep:{0:03d}{1}'.format(
                    department, suffix)
            elif type_code == 'FRREG':
                new_fb_code = 'insee-reg:{0}'.format(
                    get_code(area, 'insee-reg'))
            elif type_code == 'FRCIR':
                new_fb_code = 'ref:{0}'.format(get_code(area, 'ref-cir'))
            elif type_code == 'FRCAN':
                new_fb_code = 'can:{0}'.format(get_code(area, 'ref-can'))
            elif type_code == 'FRARR':
                new_fb_code = 'arr:{0}'.format(get_code(area, 'arr'))
            elif type_code == 'FRCOM':
                new_fb_code = 'comm:{0}'.format(get_code(area, 'comm'))
            else:
                raise Exception(
                    "Unknown area type code: '{0}'".format(type_code))
            area.codes.update_or_create(
                type=fb_code_type,
                defaults={'code': new_fb_code})
