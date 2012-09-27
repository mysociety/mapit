# This script is used after Boundary-Line has been imported to create police
# force areas in England and Wales from the other administrative areas which
# they cover.

import os, sys
sys.path.append(os.path.dirname(__file__) + '/../../../data/UK')

from optparse import make_option
from django.core.management.base import NoArgsCommand

from mapit.models import Area, Geometry, Generation, Country, Type
from police_areas_england_wales import police_areas

class Command(NoArgsCommand):
    help = 'Create police force areas from existing Boundary-Line areas'
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database'
        ),
    )

    def handle_noargs(self, **options):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        if not new_generation:
            raise Exception, "No new generation to be used for import!"

        force_type_code = 'PFL'
        force_area_type = Type.objects.get(code=force_type_code)

        england = Country.objects.get(code='E')
        wales = Country.objects.get(code='W')

        welsh_forces = ('dyfed-powys', 'gwent', 'north-wales', 'south-wales')

        for police_area in police_areas:
            force_name = police_area[0]
            force_code = force_name.lower().replace(' ', '-')
            country = wales if (force_code in welsh_forces) else england

            try:
                force = Area.objects.get(codes__code=force_code,
                                         type=force_area_type)
                print "Area matched, %s" % force
            except Area.DoesNotExist:
                force = Area(
                    # If committing, name will be overwritten by the
                    # force.names.update_or_create:
                    name            = force_name,
                    type            = force_area_type,
                    country         = country,
                    generation_low  = new_generation,
                    generation_high = new_generation,
                )
                print "New area: %s %s" % (force_type_code, force_name)

            # check that we are not about to skip a generation
            if force.generation_high and current_generation and force.generation_high.id < current_generation.id:
                raise Exception, "Area %s found, but not in current generation %s" % (force_code, current_generation)

            force.generation_high = new_generation
            if options['commit']:
                print '  saving force'
                force.save()

            # Create the Metropolitan Police Service area by unioning all the
            # London boroughs except the City of London, to avoid having to list
            # every borough in police_areas:
            if force_code == 'metropolitan':
                force_geoms = Geometry.objects.filter(areas__type__code="LBO").exclude(areas__names__name__contains="City of London")
            else:
                force_geoms = []
                # For all other forces, look for an Area matching each named
                # area in the descriptions, and union their polygons to create a
                # geometry for the force area:
                lookup = police_area[1]['lookup']
                for a in lookup:
                    lookup_type_code, lookup_name = a
                    try:
                        area = Area.objects.get(type__code=lookup_type_code,
                                                names__name__contains=lookup_name)
                        areas = area.polygons.all()
                        force_geoms.extend(areas)
                    except Area.DoesNotExist:
                        print a, 'not found'
                    except Area.MultipleObjectsReturned:
                        print 'More than one area found matching', a
                        for match in Area.objects.filter(type__code=lookup_type_code,
                                                     names__name__contains=lookup_name):
                            print ' ', match
                        print '    No polygons from these areas were used.'
            if len(force_geoms):
                print '  Geometry successfully assembled'
                if options['commit']:
                    force.polygons.clear()
                    for polygon in force_geoms:
                        force.polygons.add(polygon)
                else:
                    print '    (not saving geometry)'
            else:
                print '  No geometry created for', force_name

