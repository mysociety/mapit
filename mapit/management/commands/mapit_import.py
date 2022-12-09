# This script is used to import geometry information, from a shapefile, KML
# GeoJSON file, or GeoPackage file into MapIt.
#
# Copyright (c) 2011 UK Citizens Online Democracy. All rights reserved.
# Email: matthew@mysociety.org; WWW: http://www.mysociety.org

import logging
import sys

from django.core.management.base import LabelCommand, CommandError

import mapit.add_areas_from_file.core as add_areas_from_file
from mapit.models import Generation, Type, NameType, Country, CodeType


class Command(LabelCommand):
    help = "Import geometry data from .shp, .kml, .geojson or .gpkg files"
    label = "<SHP/KML/GeoJSON file>"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--commit",
            action="store_true",
            dest="commit",
            help="Actually update the database",
        )
        parser.add_argument(
            "--generation_id",
            action="store",
            dest="generation_id",
            help="Which generation ID should be used",
        )
        parser.add_argument(
            "--country_code",
            action="store",
            dest="country_code",
            help='Which country should be used (or "first-letter" for special UK GSS support)',
        )
        parser.add_argument(
            "--area_type_code",
            action="store",
            dest="area_type_code",
            help="Which area type should be used (specify using code)",
        )
        parser.add_argument(
            "--name_type_code",
            action="store",
            dest="name_type_code",
            help="Which name type should be used (specify using code)",
        )
        parser.add_argument(
            "--code_type",
            action="store",
            dest="code_type",
            help="Which code type should be used (specify using its code)",
        )
        parser.add_argument(
            "--name_field",
            action="store",
            dest="name_field",
            help="The field name (or names separated by comma) to look at for the area's name",
        )
        parser.add_argument(
            "--override_name",
            action="store",
            dest="override_name",
            help="The name to use for the area",
        )
        parser.add_argument(
            "--code_field",
            action="store",
            dest="code_field",
            help="The field name containing the area's ID code",
        )
        parser.add_argument(
            "--override_code",
            action="store",
            dest="override_code",
            help="The ID code to use for the area",
        )
        parser.add_argument(
            "--use_code_as_id",
            action="store_true",
            dest="use_code_as_id",
            help="Set to use the code from code_field as the MapIt ID",
        )
        parser.add_argument(
            "--preserve",
            action="store_true",
            dest="preserve",
            help="Create a new area if the name's the same but polygons differ",
        )
        parser.add_argument(
            "--new",
            action="store_true",
            dest="new",
            help="Don't look for existing areas at all, just import everything as new areas",
        )
        parser.add_argument(
            "--encoding",
            action="store",
            dest="encoding",
            help="The encoding of names in this dataset",
        )
        parser.add_argument(
            "--fix_invalid_polygons",
            action="store_true",
            dest="fix_invalid_polygons",
            help="Try to fix any invalid polygons and multipolygons found",
        )
        parser.add_argument(
            "--ignore_blank",
            action="store_true",
            help="Skip over any entry with an empty name, rather than abort",
        )

    def get_area_type(self, area_type_code, commit):
        try:
            area_type = Type.objects.get(code=area_type_code)
        except:
            type_desc = input(
                "Please give a description for area type code %s: " % area_type_code
            )
            area_type = Type(code=area_type_code, description=type_desc)
            if commit:
                area_type.save()
        return area_type

    def get_name_type(self, name_type_code, commit):
        try:
            name_type = NameType.objects.get(code=name_type_code)
        except:
            name_desc = input(
                "Please give a description for name type code %s: " % name_type_code
            )
            name_type = NameType(code=name_type_code, description=name_desc)
            if commit:
                name_type.save()
        return name_type

    def get_country(self, country_code, commit):
        try:
            country = Country.objects.get(code=country_code)
        except:
            country_name = input(
                "Please give the name for country code %s: " % country_code
            )
            country = Country(code=country_code, name=country_name)
            if commit:
                country.save()
        return country

    def get_code_type(self, code_type_code, commit):
        try:
            code_type = CodeType.objects.get(code=code_type_code)
        except:
            code_desc = input(
                "Please give a description for code type %s: " % code_type_code
            )
            code_type = CodeType(code=code_type_code, description=code_desc)
            if commit:
                code_type.save()
        return code_type

    def handle_label(self, filename, **options):
        missing_options = []
        for k in ["generation_id", "area_type_code", "name_type_code", "country_code"]:
            if options[k]:
                continue
            else:
                missing_options.append(k)
        if missing_options:
            message_start = (
                "Missing arguments "
                if len(missing_options) > 1
                else "Missing argument "
            )
            message = message_start + " ".join(
                "--{0}".format(k) for k in missing_options
            )
            raise CommandError(message)

        commit = options.get("commit", None)
        area_type = self.get_area_type(options["area_type_code"], commit)
        name_type = self.get_name_type(options["name_type_code"], commit)

        country_code = options["country_code"]
        country_from_first_letter_of_code = country_code == "first-letter"
        if country_from_first_letter_of_code:
            country = None
        else:
            country = self.get_country(country_code, commit)

        code_type_code = options.get("code_type", None)
        if code_type_code:
            code_type = self.get_code_type(code_type_code, commit)
        else:
            code_type = None

        generation_id = options["generation_id"]
        generation = Generation.objects.get(id=generation_id)

        name_field = options.get("name_field", None)
        override_name = options.get("override_name", None)
        if not name_field and not override_name:
            name_field = "Name"

        log_level = logging.DEBUG if int(options["verbosity"]) > 1 else logging.INFO
        logging.basicConfig(
            level=log_level,
            handlers=[logging.StreamHandler(stream=sys.stdout)],
        )
        logger = logging.getLogger("mapit_import")

        parameters = add_areas_from_file.Parameters(
            commit,
            generation,
            country,
            country_from_first_letter_of_code,
            area_type,
            name_type,
            code_type,
            name_field,
            override_name,
            options.get("code_field", None),
            options.get("override_code", None),
            options.get("use_code_as_id", False),
            options.get("preserve", False),
            options.get("new", False),
            options.get("encoding", "utf-8"),
            options.get("fix_invalid_polygons", False),
            options.get("ignore_blank", False),
        )
        err = parameters.validate()
        if err is not None:
            raise CommandError(err)

        try:
            add_areas_from_file.run(filename, parameters, logger)
        except add_areas_from_file.Error as e:
            raise CommandError(str(e))
