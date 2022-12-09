import os
import re
import tempfile
import zipfile

# Not using LayerMapping as want more control, but what it does is what this does
# from django.contrib.gis.utils import LayerMapping

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.contrib.gis.db.models import Collect
from mapit.models import Area, Country, Generation
from mapit.management.command_utils import (
    save_polygons,
    fix_invalid_geos_geometry,
)


class Parameters:
    def __init__(
        self,
        commit,
        generation,
        country,
        country_from_first_letter_of_code,
        area_type,
        name_type,
        code_type,
        name_field,
        override_name,
        code_field,
        override_code,
        use_code_as_id,
        preserve,
        new,
        encoding,
        fix_invalid_polygons,
        ignore_blank,
    ):
        self.commit = commit
        self.generation = generation
        self.country = country
        self.country_from_first_letter_of_code = (
            country_from_first_letter_of_code
        )
        self.area_type = area_type
        self.name_type = name_type
        self.code_type = code_type
        self.name_field = name_field
        self.override_name = override_name
        self.code_field = code_field
        self.override_code = override_code
        self.use_code_as_id = use_code_as_id
        self.preserve = preserve
        self.new = new
        self.encoding = encoding
        self.fix_invalid_polygons = fix_invalid_polygons
        self.ignore_blank = ignore_blank

    def validate(self):
        """Returns an error message as a string if the parameters are invalid.
        """
        missing_parameters_names = []
        for required_parameter_field_name in [
            "generation",
            "area_type",
            "name_type",
        ]:
            if getattr(self, required_parameter_field_name) is None:
                missing_parameters_names.append(
                    required_parameter_field_name.replace("_", " ")
                )

        if missing_parameters_names:
            return "Missing " + ", ".join(missing_parameters_names) + "."

        if self.name_field and self.override_name:
            return (
                "You can only specify one of 'name field' or 'override name'."
            )
        elif not self.name_field and not self.override_name:
            return "One of 'name field' or 'override name' must be specified."

        if self.code_field and self.override_code:
            return (
                "You can only specify one of 'code field' or 'override code'."
            )

        using_code = self.code_field or self.override_code
        if using_code and not self.code_type:
            error = (
                "If you want to save a code via a 'code field' or"
                " 'override code',"
                " you must specify 'code type'.",
            )
            return error
        if not using_code and self.code_type:
            error = (
                "You have specified 'code type' but not"
                " 'code field' or 'override code'."
            )
            return error
        if self.country and self.country_from_first_letter_of_code:
            error = (
                "You have specified a country and also selected"
                " 'country from first letter of code'"
                " - you can only choose one of these."
            )
            return error
        return None

    def __repr__(self):
        r = "{"
        for name, value in self.__dict__.items():
            r += f"\n    {name}: {value}"
        return r + "\n}"


class Error(Exception):
    pass


def run(filename, parameters, logger=None):
    if zipfile.is_zipfile(filename):
        if logger:
            logger.info("Unzipping %s" % filename)

        zipped = zipfile.ZipFile(filename)
        shp_files = [f for f in zipped.namelist() if f.endswith(".shp")]
        if len(shp_files) == 0:
            raise Error("No .shp file found in the zip file.")

        highest_level = min([f.count(os.sep) for f in shp_files])
        root_shp_files = [
            f for f in shp_files if f.count(os.sep) == highest_level
        ]
        if len(root_shp_files) > 1:
            raise Error(
                "Expected to find a single root .shp file, found %s"
                % root_shp_files
            )
        root_shp_file = root_shp_files[0]
        if logger:
            logger.info("Found %s " % root_shp_file)

        tmp_dir = tempfile.TemporaryDirectory()
        zipped.extractall(tmp_dir.name)
        filename = tmp_dir.name + os.sep + root_shp_file

    if logger:
        logger.info("Importing from %s" % filename)

    if not parameters.commit and logger:
        logger.info("(will not save to db as 'commit' not specified)")

    current_generation = Generation.objects.current()
    new_generation = parameters.generation

    ds = DataSource(filename)
    layer = ds[0]

    if (
        (parameters.override_name or parameters.override_code)
        and len(layer) > 1
        and logger
    ):
        message = (
            "You have specified an override %s and this file contains more than"
            " one feature; multiple areas with the same %s will be created"
        )
        if parameters.override_name:
            logger.warning(message % ("name", "name"))
        if parameters.override_code:
            logger.warning(message % ("code", "code"))

    for feat in layer:
        if parameters.override_name:
            name = parameters.override_name
        else:
            name = None
            for nf in parameters.name_field.split(","):
                try:
                    name = feat[nf].value
                    break
                except:
                    pass
            if name is None and not parameters.ignore_blank:
                choices = ", ".join(layer.fields)
                raise Error(
                    "Could not find name using name field '%s' - should it be"
                    " something else? It will be one of these: %s."
                    % (parameters.name_field, choices)
                )
            try:
                if name is not None and not isinstance(name, str):
                    name = name.decode(parameters.encoding)
            except:
                raise Error(
                    "Could not decode name using encoding '%s' - is it in"
                    " another encoding?"
                    % parameters.encoding
                )

        if name:
            name = re.sub(r"\s+", " ", name)
        if not name:
            if parameters.ignore_blank:
                continue
            raise Error("Could not find a name to use for area")

        code = None
        if parameters.override_code:
            code = parameters.override_code
        elif parameters.code_field:
            try:
                code = feat[parameters.code_field].value
            except:
                choices = ", ".join(layer.fields)
                raise Error(
                    "Could not find code using code field '%s' - should it be"
                    " something else? It will be one of these: %s."
                    % (parameters.code_field, choices)
                )

        if logger:
            logger.info(
                "  looking at '%s'%s" % (name, " (%s)" % code if code else "")
            )

        if parameters.country_from_first_letter_of_code and code:
            try:
                country = Country.objects.get(code=code[0])
            except Country.DoesNotExist:
                logger.warning("    No country found from first-letter")
                country = None
        else:
            country = parameters.country

        g = None
        if hasattr(feat, "geom"):
            g = feat.geom.transform(settings.MAPIT_AREA_SRID, clone=True)

        try:
            if parameters.new:  # Always want a new area
                raise Area.DoesNotExist
            if code:
                matching_message = "code %s of code type %s" % (
                    code,
                    parameters.code_type,
                )
                areas = Area.objects.filter(
                    codes__code=code, codes__type=parameters.code_type
                ).order_by("-generation_high")
            else:
                matching_message = "name %s of area type %s" % (
                    name,
                    parameters.area_type,
                )
                areas = Area.objects.filter(
                    name=name, type=parameters.area_type
                ).order_by("-generation_high")

            if len(areas) == 0:
                if logger:
                    logger.debug(
                        "    the area was not found - creating a new one"
                    )
                raise Area.DoesNotExist

            m = areas[0]
            if logger:
                logger.debug("    found the area")
            if parameters.preserve:
                # Find whether we need to create a new Area:
                previous_geos_geometry = m.polygons.aggregate(
                    Collect("polygon")
                )["polygon__collect"]
                if m.generation_high < current_generation.id:
                    # Then it was missing in current_generation:
                    if logger:
                        logger.debug(
                            "    area existed previously, but was missing from",
                            current_generation,
                        )
                    raise Area.DoesNotExist
                elif g is None:
                    if previous_geos_geometry is not None:
                        if logger:
                            logger.debug("    area is now empty")
                        raise Area.DoesNotExist
                    else:
                        if logger:
                            logger.debug("    the area has remained empty")
                elif previous_geos_geometry is None:
                    # It was empty in the previous generation:
                    if logger:
                        logger.debug(
                            "    area was empty in", current_generation
                        )
                    raise Area.DoesNotExist
                else:
                    # Otherwise, create a new Area unless the
                    # polygons were the same in current_generation:
                    previous_geos_geometry = previous_geos_geometry.simplify(
                        tolerance=0
                    )
                    new_geos_geometry = g.geos.simplify(tolerance=0)
                    create_new_area = not previous_geos_geometry.equals(
                        new_geos_geometry
                    )
                    p = (
                        previous_geos_geometry.sym_difference(
                            new_geos_geometry
                        ).area
                        / previous_geos_geometry.area
                    )
                    if logger:
                        logger.debug(
                            "    change in area is: %.03f%%" % (100 * p,)
                        )
                    if create_new_area:
                        if logger:
                            logger.debug(
                                "    the area "
                                + str(m)
                                + "has changed, creating a new area due to"
                                " --preserve"
                            )
                        raise Area.DoesNotExist
                    else:
                        if logger:
                            logger.debug("    the area remained the same")
            else:
                # If preserve is not specified, the code or the name must be unique:
                if len(areas) > 1:
                    raise Error(
                        "There was more than one area with %s, and 'preserve'"
                        " was not specified" % (matching_message,)
                    )

        except Area.DoesNotExist:
            m = Area(
                name=name,
                type=parameters.area_type,
                country=country,
                generation_low=new_generation,
                generation_high=new_generation,
            )
            if parameters.use_code_as_id and code:
                m.id = int(code)

        # check that we are not about to skip a generation
        if (
            m.generation_high
            and current_generation
            and m.generation_high.id < current_generation.id
        ):
            raise Error(
                "Area %s found, but not in current generation %s"
                % (m, current_generation)
            )
        m.generation_high = new_generation
        if parameters.fix_invalid_polygons and g is not None:
            # Make a GEOS geometry only to check for validity:
            geos_g = g.geos
            if not geos_g.valid:
                geos_g = fix_invalid_geos_geometry(geos_g)
                if geos_g is None:
                    if logger:
                        logger.info(
                            "The geometry for area %s was invalid and couldn't"
                            " be fixed" % name
                        )
                    g = None
                else:
                    g = geos_g.ogr

        poly = [g] if g is not None else []

        if parameters.commit:
            m.save()
            m.names.update_or_create(
                type=parameters.name_type, defaults={"name": name}
            )
            if code:
                m.codes.update_or_create(
                    type=parameters.code_type, defaults={"code": code}
                )
            save_polygons({m.id: (m, poly)}, write_to_stdout=False)
