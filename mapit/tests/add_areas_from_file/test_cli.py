from io import StringIO
from django.core.management import call_command, CommandError
from django.test import TestCase

from .skeletons import (
    CodeFieldAndOverride,
    CodeWithoutCodeType,
    KMLSuccess,
    MissingRequiredArguments,
    NameFieldAndOverride,
    NameFieldNotFound,
)


class Executor:
    def execute(self, filename, parameters):
        try:
            call_command(
                "mapit_import",
                filename,
                commit=parameters.commit,
                country_code="first-letter"
                if parameters.country_from_first_letter_of_code
                else parameters.country.code,
                generation_id=parameters.generation.id
                if parameters.generation
                else None,
                area_type_code=parameters.area_type.code
                if parameters.area_type
                else None,
                name_type_code=parameters.name_type.code
                if parameters.name_type
                else None,
                code_type=parameters.code_type.code
                if parameters.code_type
                else None,
                name_field=parameters.name_field,
                override_name=parameters.override_name,
                code_field=parameters.code_field,
                override_code=parameters.override_code,
                use_code_as_id=parameters.use_code_as_id,
                preserve=parameters.preserve,
                new=parameters.new,
                encoding=parameters.encoding,
                fix_invalid_polygons=parameters.fix_invalid_polygons,
                ignore_blank=parameters.ignore_blank,
                # Comment these lines to see these streams when running tests.
                stderr=StringIO(),
                stdout=StringIO(),
            )
        except CommandError as e:
            return True, str(e)

        return False, ""


class MissingRequiredArgumentsTest(
    Executor, MissingRequiredArguments, TestCase
):
    def expected_error_message(self):
        return (
            "Missing arguments --generation_id --area_type_code "
            "--name_type_code"
        )


class NameFieldAndOverrideTest(Executor, NameFieldAndOverride, TestCase):
    pass


class CodeFieldAndOverrideTest(Executor, CodeFieldAndOverride, TestCase):
    pass


class CodeWithoutCodeTypeTest(Executor, CodeWithoutCodeType, TestCase):
    pass


# No tests for prompt flows.


class NameFieldNotFoundTest(Executor, NameFieldNotFound, TestCase):
    pass


class KMLSuccessTest(Executor, KMLSuccess, TestCase):
    pass
