import os

from django.conf import settings
from django.contrib.gis.gdal.prototypes import ds

from mapit.add_areas_from_file import core
from mapit.models import Area, CodeType, Country, Generation, NameType, Type


def england():
    v, _ = Country.objects.get_or_create(code="E", name="England")
    return v


def generation():
    v, _ = Generation.objects.get_or_create(
        active=True, description="Test generation"
    )
    return v


def big_area_type():
    v, _ = Type.objects.get_or_create(
        code="BIG",
        description="A large test area",
    )
    return v


def ordnance_survey_name_type():
    v, _ = NameType.objects.get_or_create(
        code="O",
        description="Ordnance survey name",
    )
    return v


def gss():
    v, _ = CodeType.objects.get_or_create(
        code="GSS",
        description="gss",
    )
    return v


def fixtures_dir():
    return os.path.join(settings.BASE_DIR, "mapit", "tests", "fixtures")


def example_kml_file():
    return os.path.join(fixtures_dir(), "example.kml")


class Base(object):
    def setUp(self):
        # Forcefully register a GDAL datasource driver, because Django has a
        # bug where it assumes that any existing drivers mean they're all
        # available, which doesn't seem to be the case.
        if not ds.get_driver_count():
            ds.register_all()

    def filename(self):
        raise Exception("Not implemented")

    def parameters(self):
        raise Exception("Not implemented")

    def expected_error_message(self):
        raise Exception("Not implemented")

    def execute(self, filename, parameters):
        raise Exception("Not implemented")

    def should_fail(self):
        return False

    def check_database_state(self):
        pass

    def check_error_message(self, expected, error_message):
        self.assertIn(expected, error_message)

    def test(self):
        failed, error_message = self.execute(self.filename(), self.parameters())

        if failed != self.should_fail():
            message = "Failed " if failed else "Passed "
            message += "unexpectedly with message '%s'" % error_message
            self.fail(message)

        if failed:
            self.check_error_message(
                self.expected_error_message(), error_message
            )
        self.check_database_state()


class WithKML(object):
    def filename(self):
        return example_kml_file()


class ShouldFail(object):
    def should_fail(self):
        return True

    def check_database_state(self):
        self.assertEqual(Area.objects.count(), 0)


class MissingRequiredArguments(WithKML, ShouldFail, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=None,
            country=england(),
            country_from_first_letter_of_code=False,
            area_type=None,
            name_type=None,
            code_type=None,
            name_field="Name",
            override_name=None,
            code_field=None,
            override_code=None,
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )


class NameFieldAndOverride(WithKML, ShouldFail, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=generation(),
            country=england(),
            country_from_first_letter_of_code=False,
            area_type=big_area_type(),
            name_type=ordnance_survey_name_type(),
            code_type=None,
            name_field="Name",
            override_name="Another one",
            code_field=None,
            override_code=None,
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )

    def expected_error_message(self):
        return "You can only specify one of 'name field' or 'override name'."


class CodeFieldAndOverride(WithKML, ShouldFail, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=generation(),
            country=england(),
            country_from_first_letter_of_code=False,
            area_type=big_area_type(),
            name_type=ordnance_survey_name_type(),
            code_type=None,
            name_field="Name",
            override_name=None,
            code_field="Code",
            override_code="Another one",
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )

    def expected_error_message(self):
        return "You can only specify one of 'code field' or 'override code'."


class CodeWithoutCodeType(WithKML, ShouldFail, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=generation(),
            country=england(),
            country_from_first_letter_of_code=False,
            area_type=big_area_type(),
            name_type=ordnance_survey_name_type(),
            code_type=None,
            name_field="Name",
            override_name=None,
            code_field=None,
            override_code="Another one",
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )

    def expected_error_message(self):
        return (
            "If you want to save a code via a 'code field' or 'override code',"
            " you must specify 'code type'."
        )


class CodeTypeWithoutCode(WithKML, ShouldFail, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=generation(),
            country=england(),
            country_from_first_letter_of_code=False,
            area_type=big_area_type(),
            name_type=ordnance_survey_name_type(),
            code_type=gss(),
            name_field="Name",
            override_name=None,
            code_field=None,
            override_code=None,
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )

    def expected_error_message(self):
        return (
            "You have specified 'code type' but not 'code field' or 'override"
            " code'."
        )


class CountryAndFromFirstLetter(WithKML, ShouldFail, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=generation(),
            country=england(),
            country_from_first_letter_of_code=True,
            area_type=big_area_type(),
            name_type=ordnance_survey_name_type(),
            code_type=None,
            name_field="Name",
            override_name=None,
            code_field=None,
            override_code=None,
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )

    def expected_error_message(self):
        return (
            "You have specified a country and also selected "
            "'country from first letter of code' "
            "- you can only choose one of these."
        )


class NameFieldNotFound(WithKML, ShouldFail, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=generation(),
            country=england(),
            country_from_first_letter_of_code=False,
            area_type=big_area_type(),
            name_type=ordnance_survey_name_type(),
            code_type=None,
            name_field="Invalid",
            override_name=None,
            code_field=None,
            override_code=None,
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )

    def expected_error_message(self):
        return (
            "Could not find name using name field 'Invalid' "
            "- should it be something else? It will be one "
            "of these:"
        )


class KMLSuccess(WithKML, Base):
    def parameters(self):
        return core.Parameters(
            commit=True,
            generation=generation(),
            country=england(),
            country_from_first_letter_of_code=False,
            area_type=big_area_type(),
            name_type=ordnance_survey_name_type(),
            code_type=None,
            name_field="Name",
            override_name=None,
            code_field=None,
            override_code=None,
            use_code_as_id=False,
            preserve=False,
            new=False,
            encoding=False,
            fix_invalid_polygons=False,
            ignore_blank=False,
        )

    def check_database_state(self):
        self.assertEqual(Area.objects.count(), 1)
        area = Area.objects.all()[0]
        self.assertEqual(area.name, "London")
        self.assertEqual(area.country.name, england().name)
        self.assertEqual(area.generation_low.id, generation().id)
        self.assertEqual(area.generation_high.id, generation().id)
        self.assertEqual(area.type.code, "BIG")
