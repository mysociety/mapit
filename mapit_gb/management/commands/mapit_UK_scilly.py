# This script is used to fix up the Isles of Scilly for historic reasons.

from django.core.management.base import BaseCommand, CommandError
from mapit.models import Area, Type


class Command(BaseCommand):
    help = 'Make sure the Isles of Scilly and its parishes are in their own type'

    def add_arguments(self, parser):
        parser.add_argument('--commit', action='store_true', dest='commit', help='Actually update the database')

    def handle(self, **options):
        isles_type = Type.objects.get(code='COI')
        parish_type = Type.objects.get(code='COP')
        ward_type = Type.objects.get(code='UTW')

        if not options['commit']:
            print "DRY RUN"

        try:
            council = Area.objects.get(codes__type__code='gss', codes__code='E06000053')
        except Area.DoesNotExist:
            raise CommandError('Could not find Scilly Isles, please import it first')
        print 'Scilly Isles:',
        if council.type != isles_type:
            print "Updating from %s to %s" % (council.type.code, isles_type.code)
            council.type = isles_type
            if options['commit']:
                council.save()
        else:
            print 'Already %s' % isles_type.code

        wards = council.children.filter(type=ward_type)
        count_wards = wards.count()
        print 'Parishes:',
        if count_wards == 5:
            print "Updating from %s to %s" % (ward_type.code, parish_type.code)
            if options['commit']:
                wards.update(type=parish_type)
        elif count_wards == 0:
            print 'Already %s' % parish_type.code
        else:
            raise CommandError('Scilly Isles should have 0 or 5 ward children')
