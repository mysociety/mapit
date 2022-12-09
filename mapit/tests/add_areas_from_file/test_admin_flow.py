import html
import re

from http import HTTPStatus

from django.contrib.auth.models import User
from django.test import TestCase

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


def get_choice_for_model(page_html, model):
    # Assumes the model string representation is unique to the page.
    pattern = r'<option value="(\d+)">%s</option>' % re.escape(str(model))
    match = re.search(pattern, page_html)
    return match.group(1)


class Executor:
    def execute(self, filename, parameters):
        self.superuser = User.objects.create_user("superuser", "", "password")
        self.superuser.is_staff = True
        self.superuser.is_superuser = True
        self.superuser.save()
        self.client.login(username=self.superuser.username, password="password")

        add_areas_from_file_url = "/admin/add-areas-from-file/"
        response = self.client.get(add_areas_from_file_url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        page_html = response.content.decode("utf-8")

        with open(filename, "r") as f:
            payload = {"file": f}
            for parameter_name in [
                "area_type",
                "country",
                "generation",
                "name_type",
            ]:
                value = getattr(parameters, parameter_name)
                if value is not None:
                    payload[parameter_name] = get_choice_for_model(
                        page_html, value
                    )

            if parameters.code_type:
                payload["code_type"] = get_choice_for_model(
                    page_html, parameters.code_type
                )

            def add_parameter_to_payload_if_set(parameter_name):
                value = getattr(parameters, parameter_name, None)
                if value:
                    payload[parameter_name] = value

            add_parameter_to_payload_if_set("commit")
            add_parameter_to_payload_if_set("country_from_first_letter_of_code")
            add_parameter_to_payload_if_set("name_field")
            add_parameter_to_payload_if_set("override_name")
            add_parameter_to_payload_if_set("code_field")
            add_parameter_to_payload_if_set("override_code")
            add_parameter_to_payload_if_set("use_code_as_id")
            add_parameter_to_payload_if_set("preserve")
            add_parameter_to_payload_if_set("new")
            add_parameter_to_payload_if_set("encoding")
            add_parameter_to_payload_if_set("fix_invalid_polygons")
            add_parameter_to_payload_if_set("ignore_blank")

            response = self.client.post(
                add_areas_from_file_url, payload, follow=True
            )

        page_html = response.content.decode("utf-8")

        if (
            response.status_code != HTTPStatus.OK
            or "errorlist" in page_html
            or "Command failed." in page_html
        ):
            return True, page_html

        return False, None

    def check_error_message(self, expected, page_html):
        if expected in page_html:
            return
        if expected in html.unescape(page_html):
            return
        # We can't find a match; fail in a way with helpful output.
        self.assertIn(expected, page_html)


class MissingRequiredArgumentsTest(
    Executor, MissingRequiredArguments, TestCase
):
    def expected_error_message(self):
        return "This field is required."


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
