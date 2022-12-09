import io
import logging

from django.core.exceptions import ValidationError
from django.forms import (
    BooleanField,
    CharField,
    FileField,
    Form,
    ModelChoiceField,
)
from django.shortcuts import render
from mapit.models import (
    Generation,
    Type,
    NameType,
    CodeType,
    Country,
)
from mapit.add_areas_from_file import core


class Form(Form):
    commit = BooleanField(
        help_text="Make changes to the database.",
        required=False,
    )
    file = FileField(
        help_text=(
            "A .kml, .geojson or .gpkg file or a zipped folder"
            " containing a .shp at the root of the folder along with the"
            " sibling files."
        ),
        required=True,
    )
    area_type = ModelChoiceField(queryset=Type.objects.all(), required=True)
    generation = ModelChoiceField(
        queryset=Generation.objects.all(), required=True
    )
    name_type = ModelChoiceField(queryset=NameType.objects.all(), required=True)
    country = ModelChoiceField(queryset=Country.objects.all(), required=False)
    country_from_first_letter_of_code = BooleanField(
        help_text=(
            "Lookup the country from from the first letter of an area's code."
            " E.g. GSS codes in the UK start with E/N/W/S for the constituent"
            " country. Can be used instead of directly specifying a country."
        ),
        required=False,
    )
    name_field = CharField(
        help_text=(
            "A field name to use to lookup the name of an area. You can"
            " specify multiple field names separated by commas and the name"
            " will be taken from the first match."
        ),
        required=False,
    )
    override_name = CharField(
        help_text=(
            "A name to use for an area instead of looking up via 'Name field'."
        ),
        required=False,
    )
    code_type = ModelChoiceField(
        queryset=CodeType.objects.all(), required=False
    )
    code_field = CharField(
        help_text=(
            "A field name to use to lookup the code of an area."
            " Supports one field name only."
        ),
        required=False,
    )
    override_code = CharField(
        help_text=(
            "A code to use for all areas found. Can be used instead of 'Code"
            " field'."
        ),
        required=False,
    )
    use_code_as_id = BooleanField(
        help_text="Use an area's code as it's ID in MapIt.",
        required=False,
    )
    new = BooleanField(
        help_text=(
            "Add all areas as if they are new and don't compare them against"
            " existing areas."
        ),
        required=False,
    )
    preserve = BooleanField(
        help_text=(
            "Create a new area when an area matches an existing area but the"
            " polygons differ. Only applies when 'New' is not set."
        ),
        required=False,
    )
    encoding = CharField(
        help_text=(
            "The encoding to use to decode area names, if needed e.g. utf-8."
        ),
        required=False,
    )
    fix_invalid_polygons = BooleanField(
        help_text=(
            "Try to fix invalid any invalid polygons and multipolygons found."
        ),
        required=False,
    )
    ignore_blank = BooleanField(
        help_text=(
            "Skip over an area with a blank name rather than abort the process."
        ),
        required=False,
    )

    def clean(self):
        parameters = self.as_parameters()
        err = parameters.validate()
        if err:
            raise ValidationError(err)

    def as_parameters(self):
        return core.Parameters(
            self.cleaned_data.get("commit", None),
            self.cleaned_data.get("generation", None),
            self.cleaned_data.get("country", None),
            self.cleaned_data.get("country_from_first_letter_of_code", None),
            self.cleaned_data.get("area_type", None),
            self.cleaned_data.get("name_type", None),
            self.cleaned_data.get("code_type", None),
            self.cleaned_data.get("name_field", None),
            self.cleaned_data.get("override_name", None),
            self.cleaned_data.get("code_field", None),
            self.cleaned_data.get("override_code", None),
            self.cleaned_data.get("use_code_as_id", None),
            self.cleaned_data.get("preserve", None),
            self.cleaned_data.get("new", None),
            self.cleaned_data.get("encoding", None),
            self.cleaned_data.get("fix_invalid_polygons", None),
            self.cleaned_data.get("ignore_blank", None),
        )


def view(request):
    form = Form(request.POST or None, request.FILES)
    if form.is_valid():
        parameters = form.as_parameters()
        f = request.FILES["file"]
        stream, logger = stream_logger()
        error_message = None
        try:
            core.run(f.temporary_file_path(), parameters, logger=logger)
        except core.Error as e:
            error_message = str(e)
        return render(
            request,
            "mapit/add-areas-from-file/result.html",
            {
                "parameters": str(form.as_parameters()),
                "logs": stream.getvalue(),
                "error_message": error_message,
            },
        )
    return render(
        request,
        "mapit/add-areas-from-file/form.html",
        {
            "form": form,
        },
    )


def stream_logger():
    stream = io.StringIO()
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream)
    logger.addHandler(handler)
    return stream, logger
