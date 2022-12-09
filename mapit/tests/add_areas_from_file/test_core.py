from django.test import TestCase
from mapit.add_areas_from_file.core import Error as CoreError, run

from .skeletons import (
    CodeFieldAndOverride,
    CodeTypeWithoutCode,
    CodeWithoutCodeType,
    CountryAndFromFirstLetter,
    KMLSuccess,
    MissingRequiredArguments,
    NameFieldAndOverride,
    NameFieldNotFound,
)


class Executor:
    def execute(self, filename, parameters):
        error_message = parameters.validate()
        if error_message:
            return True, error_message
        try:
            run(filename, parameters)
        except CoreError as e:
            return True, str(e)
        return False, ""


class MissingRequiredArgumentsTest(
    Executor, MissingRequiredArguments, TestCase
):
    def expected_error_message(self):
        return "Missing generation, area type, name type."


class NameFieldAndOverrideTest(Executor, NameFieldAndOverride, TestCase):
    pass


class CodeFieldAndOverrideTest(Executor, CodeFieldAndOverride, TestCase):
    pass


class CodeWithoutCodeTypeTest(Executor, CodeWithoutCodeType, TestCase):
    pass


class CodeTypeWithoutCodeTest(Executor, CodeTypeWithoutCode, TestCase):
    pass


class CountryAndFromFirstLetterTest(
    Executor, CountryAndFromFirstLetter, TestCase
):
    pass


class NameFieldNotFoundTest(Executor, NameFieldNotFound, TestCase):
    pass


class KMLSuccessTest(Executor, KMLSuccess, TestCase):
    pass
