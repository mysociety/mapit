# -*- coding: utf-8 -*-

from optparse import make_option

from django.contrib.gis.geos import GEOSGeometry
from django.core.management.base import BaseCommand, CommandError

from mapit.management.command_utils import save_polygons
from mapit.models import Area, Generation, Geometry, Type

import unicodedata

def remove_accents(input_str):
    nkfd_form = unicodedata.normalize('NFKD', input_str)
    return u"".join([c for c in nkfd_form if not unicodedata.combining(c)])

class Command(BaseCommand):

    help = u'Create the Sección Electoral areas in the Buenos Aires province'

    option_list = BaseCommand.option_list + (
        make_option(
            '--commit',
            action='store_true',
            dest='commit',
            help='Actually update the database',
        ),
    )

    def handle(self, **options):

        # This list of departments is from this Wikipedia page:
        # https://es.wikipedia.org/wiki/Secciones_electorales_de_la_Provincia_de_Buenos_Aires
        # with some slight name changes to make sure that they match
        # the department names that are already in MapIt.

        electoral_sections = {
            '1': [
                u"Campana",
                u"Escobar",
                u"General Las Heras",
                u"General Rodríguez",
                u"General San Martín",
                u"Hurlingham",
                u"Ituzaingó",
                u"José C Paz",
                u"Luján",
                u"Marcos Paz",
                u"Mercedes",
                u"Merlo",
                u"Moreno",
                u"Morón",
                u"Malvinas Argentinas",
                u"Navarro",
                u"Pilar",
                u"San Fernando",
                u"San Isidro",
                u"San Miguel",
                u"Suipacha",
                u"Tigre",
                u"Tres de Febrero",
                u"Vicente López",
            ],
            '2': [
                u"Arrecifes",
                u"Baradero",
                u"Capitán Sarmiento",
                u"Carmen de Areco",
                u"Colón",
                u"Exaltación de la Cruz",
                u"Pergamino",
                u"Ramallo",
                u"Rojas",
                u"Salto",
                u"San Andrés de Giles",
                u"San Antonio de Areco",
                u"San Nicolás",
                u"San Pedro",
                u"Zárate",
            ],
            '3': [
                u"Almirante Brown",
                u"Avellaneda",
                u"Berazategui",
                u"Berisso",
                u"Brandsen",
                u"Cañuelas",
                u"Ensenada",
                u"Esteban Echeverría",
                u"Ezeiza",
                u"Florencio Varela",
                u"La Matanza",
                u"Lanús",
                u"Lobos",
                u"Lomas de Zamora",
                u"Magdalena",
                u"Presidente Perón",
                u"Punta Indio",
                u"Quilmes",
                u"San Vicente",
            ],
            '4': [
                u"Alberti",
                u"Bragado",
                u"Carlos Casares",
                u"Carlos Tejedor",
                u"Chacabuco",
                u"Chivilcoy",
                u"Florentino Ameghino",
                u"General Arenales",
                u"General Pinto",
                u"General Viamonte",
                u"General Villegas",
                u"Hipólito Yrigoyen",
                u"Junín",
                u"Leandro N Alem",
                u"Lincoln",
                u"9 de Julio",
                u"Pehuajó",
                u"Rivadavia",
                u"Trenque Lauquen",
            ],
            '5': [
                u"Ayacucho",
                u"Balcarce",
                u"Castelli",
                u"Chascomús",
                u"Dolores",
                u"General Alvarado",
                u"General Belgrano",
                u"General Guido",
                u"General Lavalle",
                u"General Juan Madariaga",
                u"General Paz",
                u"General Pueyrredón",
                u"La Costa",
                u"Las Flores",
                # FIXME: Lezama (the newest department) is missing
                # from the official department shapefiles:
                # u"Lezama",
                u"Lobería",
                u"Maipú",
                u"Mar Chiquita",
                u"Monte",
                u"Necochea",
                u"Pila",
                u"Pinamar",
                u"Rauch",
                u"San Cayetano",
                u"Tandil",
                u"Tordillo",
                u"Villa Gesell",
            ],
            '6': [
                u"Adolfo Alsina",
                u"Adolfo Gonzales Chaves",
                u"Bahía Blanca",
                u"Benito Juárez",
                u"Coronel Dorrego",
                u"Coronel Pringles",
                u"Coronel de Marina Leonardo Rosales",
                u"Coronel Suárez",
                u"Daireaux",
                u"Guaminí",
                u"General la Madrid",
                u"Laprida",
                u"Monte Hermoso",
                u"Patagones",
                u"Pellegrini",
                u"Puan",
                u"Saavedra",
                u"Salliqueló",
                u"Tres Arroyos",
                u"Tres Lomas",
                u"Tornquist",
                u"Villarino",
            ],
            '7': [
                u"Azul",
                u"Bolívar",
                u"General Alvear",
                u"Olavarría",
                u"Roque Pérez",
                u"Saladillo",
                u"Tapalqué",
                u"25 de Mayo",
            ],
            '8': [
                u"La Plata",
            ]
        }

        province = Area.objects.get(name='BUENOS AIRES', type__code='PRV')
        new_generation = Generation.objects.new()
        departments_in_province = sorted(
            Area.objects.intersect(
                'intersects',
                province,
                ['DPT'],
                new_generation
            ),
            key=lambda a: a.name
        )
        for d in departments_in_province:
            print d.name.encode('utf-8')

        def get_department_from_name(name):
            department_name_without_accents = remove_accents(department_name)
            uppercased = department_name.upper()
            uppercased_without_accents = department_name_without_accents.upper()
            print u"Looking up {0} or {1}".format(
                uppercased, uppercased_without_accents
            )
            for department in departments_in_province:
                if department.name in (uppercased, uppercased_without_accents):
                    return department

        for section, department_names in electoral_sections.items():
            departments = []
            for department_name in department_names:
                d = get_department_from_name(department_name)
                if not d:
                    message = u"Couldn't find the department: {0}"
                    raise CommandError(message.format(department_name))
                departments.append(d)
            area_ids = [a.id for a in departments]
            geometries = Geometry.objects.filter(area__id__in=area_ids)
            geometry_union = geometries.unionagg()
            name_format = u"{section}º Sección Electoral de la Provincia de Buenos Aires"
            sel_name = name_format.format(section=section)
            try:
                area = Area.objects.get(name=sel_name)
                print u"Found existing area {area} with ID {area.id}".format(
                    area=area
                )
            except Area.DoesNotExist:
                area = Area(
                    name=sel_name,
                    type=Type.objects.get(code='SEL'),
                    generation_low=new_generation,
                    generation_high=new_generation,
                )
            area.generation_high = new_generation
            if options['commit']:
                ogr_geometry_list = [GEOSGeometry(geometry_union).ogr]
                area.save()
                save_polygons(
                    {
                        'ignored': (area, ogr_geometry_list)
                    }
                )
