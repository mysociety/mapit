# This script adds GSS codes to existing CED areas
# based on a mapping from ONS e.g.
# https://geoportal.statistics.gov.uk/documents/ons::county-electoral-division-to-county-may-2021-lookup-for-england/about
# The XLSX file should be converted to CSV before being used with this script.

from django.core.management.base import LabelCommand, CommandError
from django.db import transaction
from csv import DictReader

from mapit.models import Area, Generation, CodeType

# Some names are slightly different in Boundary-Line vs the ONS CSV,
# so fix those up here for the DB lookup
NAME_FIXES = {
    # name in ONS CSV : name of area already in DB (from BL)
    "Mendip Hiils ED": "Mendip Hills ED",
    "Hollington & Wishing Tree ED": "Hollington &Wishing Tree ED",
    "Maze Hill & West St. Leonards ED": "Maze Hill &West St. Leonards ED",
    "Uckfield South with Framfield ED": "Uckfield South With Framfield ED",
    "Grove & Wantage ED": "Grove and Wantage ED",
    "Hendreds &Harwell ED": "Hendreds and Harwell ED",
    "Sutton Courtenay & Marcham ED": "Sutton Courtenay and Marcham ED",
    "Bishops Stortford East ED": "Bishop's Stortford East ED",
    "Bishops Stortford Rural ED": "Bishop's Stortford Rural ED",
    "Bishops Stortford West ED": "Bishop's Stortford West ED",
}

# Some areas don't exist in MapIt at all, so should be ignored
IGNORED_NAMES = {
    "Thorpe St. Andrew ED (DET)",
    "Lightwater, West End and Bisley ED (DET)",
}


class Command(LabelCommand):
    help = "Adds GSS codes to CED areas in the active generation"
    label = "<CSV file>"

    commit = False

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--commit",
            action="store_true",
            dest="commit",
            default=self.commit,
            help="Commit changes to database",
        )
        parser.add_argument(
            "--generation",
            dest="generation",
            type=int,
            help=f"Generation to search for CED areas in (default {Generation.objects.current().id})",
            default=Generation.objects.current().id,
        )
        parser.add_argument(
            "--code-field",
            dest="code_field",
            type=str,
            required=True,
            help="CSV field to get GSS codes from",
        )
        parser.add_argument(
            "--parent-code-field",
            dest="parent_code_field",
            type=str,
            required=True,
            help="CSV field to get parent GSS codes from",
        )
        parser.add_argument(
            "--name-field",
            dest="name_field",
            type=str,
            required=True,
            help="CSV field to get area names from",
        )

    def handle_label(self, filename, **options):
        self.commit = options["commit"]

        with open(filename) as f:
            self.handle_rows(
                DictReader(f),
                options["code_field"],
                options["name_field"],
                options["parent_code_field"],
                options["generation"],
            )

    @transaction.atomic
    def handle_rows(self, csv, code_field, name_field, parent_code_field, generation):
        gss = CodeType.objects.get(code="gss")

        for row in csv:
            name = NAME_FIXES.get(row[name_field], row[name_field])

            if name in IGNORED_NAMES:
                continue

            params = dict(
                type__code="CED",
                names__type__code="O",
                names__name=name,
                parent_area__codes__code=row[parent_code_field],
                generation_low__lte=generation,
                generation_high__gte=generation,
            )
            try:
                area = Area.objects.get(**params)
            except Area.DoesNotExist:
                raise CommandError(f"Couldn't find existing CED area '{name}'")

            area.codes.get_or_create(type=gss, code=row[code_field])
            print(f"{name}: {row[code_field]}")

        if not self.commit:
            transaction.set_rollback(True)
