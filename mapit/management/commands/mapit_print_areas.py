# For each generation, show every area, grouped by type

from django.core.management.base import BaseCommand
from mapit.models import Area, Generation, Type


class Command(BaseCommand):
    help = 'Show all areas by generation and area type'

    def handle(self, **options):
        for g in Generation.objects.all().order_by('id'):
            print(g)
            for t in Type.objects.all().order_by('code'):
                qs = Area.objects.filter(type=t,
                                         generation_high__gte=g,
                                         generation_low__lte=g)
                print("  %s (number of areas: %d)" % (t, qs.count()))
                for a in qs:
                    print("     %s" % a)
