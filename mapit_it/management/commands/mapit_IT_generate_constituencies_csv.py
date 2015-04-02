from __future__ import unicode_literals
import json
import logging
from optparse import make_option
import os
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import NoArgsCommand, CommandError
from django.db.models import Q
import sys
from mapit.models import Area, Generation, Geometry, Type, CodeType, Country, Code

__author__ = 'guglielmo'

class Command(NoArgsCommand):
    """This management command can be used to generate
    the CSV stream to import constituencies using the mapit_import_area_union tasks

    This is needed to avoid inputing manually IDs that may change from instance to instance
    """

    help = 'Generate constituencies CSV'
    option_list = NoArgsCommand.option_list + (
        make_option(
            '--output-file',
            default='stdout',
            dest='output_file', help='Path to CSV file containing the output'
        ),
    )
    FORMAT = "[%(asctime)s] %(levelname)s - %(message)s"
    logging.basicConfig(format=FORMAT, level=logging.INFO)

    def handle_noargs(self, **options):
        """
        A wrapper launching subtasks for CIRCCAM and CIRCEU
        constituencies
        :param options: not used
        :return:        void
        """

        if options['output_file'] == 'stdout':
            csv_out = sys.stdout
        else:
            csv_out = open(options['output_file'], 'w')

        logging.info("Generating constituencies for national elections (camera)")
        self.handle_circcam(file=csv_out)

        logging.info("Generating constituencies for european elections")
        self.handle_circeu(file=csv_out)

        csv_out.close()

        logging.info("Finishing")


    def handle_circcam(self, file=sys.stdout):
        """
        Add constituencies for political national elections at La Camera.

        :param constituencies: data structure containing definitions
        :param country:        the Country object to assign to all areas
        :param generation:     the Generation object, the areas will belong to
        :return:               void
        """
        logging.info("Generating constituencies for la Camera's general elections")

        constituencies= [
            { 'name': 'Piemonte 1', 'region_name': 'Piemonte',
              'provinces': ['Torino'], 'filter_type': 'include' },
            { 'name': 'Piemonte 2', 'region_name': 'Piemonte',
              'provinces': ['Torino'], 'filter_type': 'exclude' },
            { 'name': 'Lombardia 1', 'region_name': 'Lombardia',
              'provinces': ['Milano', 'Monza e della Brianza'], 'filter_type': 'include' },
            { 'name': 'Lombardia 1', 'region_name': 'Lombardia',
              'provinces': ['Bergamo', 'Brescia', 'Como', 'Sondrio', 'Varese', 'Lecco'], 'filter_type': 'include' },
            { 'name': 'Lombardia 2', 'region_name': 'Lombardia',
              'provinces': ['Pavia', 'Lodi', 'Cremona', 'Mantova'], 'filter_type': 'include' },
            { 'name': 'Veneto 1', 'region_name': 'Veneto',
              'provinces': ['Venezia', 'Treviso', 'Belluno'], 'filter_type': 'include' },
            { 'name': 'Veneto 2', 'region_name': 'Veneto',
              'provinces': ['Venezia', 'Treviso', 'Belluno'], 'filter_type': 'exclude' },
            { 'name': 'Lazio 1', 'region_name': 'Lazio',
              'provinces': ['Roma'], 'filter_type': 'include' },
            { 'name': 'Lazio 2', 'region_name': 'Lazio',
              'provinces': ['Roma'], 'filter_type': 'exclude' },
            { 'name': 'Campania 1', 'region_name': 'Campania',
              'provinces': ['Napoli'], 'filter_type': 'include' },
            { 'name': 'Campania 2', 'region_name': 'Campania',
              'provinces': ['Napoli'], 'filter_type': 'exclude' },
            { 'name': 'Sicilia 1', 'region_name': 'Sicilia',
              'provinces': ['Palermo', 'Trapani', 'Agrigento', 'Caltanissetta'], 'filter_type': 'include' },
            { 'name': 'Sicilia 2', 'region_name': 'Sicilia',
              'provinces': ['Palermo', 'Trapani', 'Agrigento', 'Caltanissetta'], 'filter_type': 'exclude' },
        ]
        for const in constituencies:
            self.emit_csv(
                {'parent_area__type__code': 'REG',
                 'parent_area__name': const['region_name']},
                'CIRCCAM', const['name'],
                const['provinces'],
                filter_type=const['filter_type'], file=file
            )


        regioni_names = Area.objects.filter(type__code='REG').exclude(
            name__in=(
                'Piemonte', 'Lombardia', 'Veneto',
                'Lazio', 'Campania', 'Sicilia'
            )
        ).values_list('name', flat=True)
        for name in regioni_names:
            self.emit_csv(
                {'parent_area__name': name,
                 'parent_area__type__code': 'REG'},
                'CIRCCAM', name, [],
                filter_type='all', file=file
            )



    def handle_circeu(self, file=sys.stdout):
        """
        Add constituencies for european elections.
        :return:               string
        """

        logging.info("Generating constituencies for European Parliament's elections")

        constituencies= [
            { 'name': 'Nord-occidentale',
              'regions': ["Valle d'Aosta", "Liguria", "Piemonte", "Lombardia"] },
            { 'name': 'Nord-orientale',
              'regions': ["Emilia-Romagna", "Friuli Venezia Giulia", "Trentino-Alto adige", "Veneto"] },
            { 'name': 'Centrale',
              'regions': ["Toscana", "Umbria", "Marche", "Lazio"] },
            { 'name': 'Meridionale',
              'regions': ["Abruzzo", "Molise", "Campania", "Basilicata", "Puglia", "Calabria"] },
            { 'name': 'Isole',
              'regions': ["Sicilia", "Sardegna"] },
        ]
        for const in constituencies:
            self.emit_csv(
                {'type__code': 'REG'},
                'CIRCEU', const['name'],
                const['regions'],
                filter_type='include', file=file
            )


    def emit_csv(self, old_areas_filters, const_code, const_name, old_areas_names, filter_type='all', file=sys.stdout):
        """
        Emit CSV line to file

        :param parent_area_filters: dict   - django-orm filters to select the parent area, as dict
                                             ('name': 'Lombardia', 'type__code': 'REG')
        :param circ_code:           string - New constitution code (CIRCCAM)
        :param circ_name:           string - New constitution name (Piemonte 1)
        :param old_areas_names:     list   - List or Tuple of old areas names (must be uniques among old_area children)
        :param filter_type:         string - Type of filter (may be 'all', 'include' or 'exclude'
        :param file:                file   - the file the stream must be sent to
        :return:                    void
        """

        r = Area.objects.filter(**old_areas_filters)
        new_area_csv = ";{0};{1};".format(const_code, const_name)
        if filter_type == 'all':
            old_areas_csv = ",".join(["{0} {1}".format(id, name) for id,name in r.values_list('id', 'name')])
        elif filter_type == 'exclude':
            old_areas_csv = ",".join(["{0} {1}".format(id, name) for id,name in r.exclude(name__in=old_areas_names).values_list('id', 'name')])
        else:
            old_areas_csv = ",".join(["{0} {1}".format(id, name) for id,name in r.filter(name__in=old_areas_names).values_list('id', 'name')])

        file.write(
            new_area_csv +
            old_areas_csv +
            "\n"
        )

