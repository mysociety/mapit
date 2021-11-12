from mapit.management.commands.mapit_import_postal_codes import Command

from django.contrib.gis.geos import Point

from mapit_labour.models import UPRN
from mapit.models import CodeType

CODE_TYPE_MAP = {
    1: "uprn",
    2: "parent_uprn",
    3: "udprn",
    4: "usrn",
    5: "toid",
    6: "classification_code",
    7: "easting",
    8: "northing",
    9: "latitude",
    10: "longitude",
    11: "rpc",
    12: "last_update_date",
    13: "single_line_address",
    14: "po_box",
    15: "organisation",
    16: "sub_building",
    17: "building_name",
    18: "building_number",
    19: "street_name",
    20: "locality",
    21: "town_name",
    22: "post_town",
    23: "island",
    24: "postcode",
    25: "delivery_point_suffix",
    26: "gss_code",
    27: "change_code",
}


class Command(Command):
    help = "Imports UK UPRNs from AddressBase Core"
    label = "<AddressBase Core CSV file>"
    option_defaults = {
        "header-row": True,
        "strip": True,
        "srid": 27700,
        "coord-field-lon": 7,
        "coord-field-lat": 8,
    }

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            "--postcode-field",
            action="store",
            dest="postcode-field",
            default=24,
            help="The column of the CSV containing the postal code (default 24)",
        )

    def process(self, *args, **kwargs):
        self.code_types = {c.code: c for c in CodeType.objects.all()}
        super(Command, self).process(*args, **kwargs)

    def handle_row(self, row, options):
        if not options["coord-field-lon"]:
            options["coord-field-lon"] = int(options["coord-field-lat"]) + 1
        lat = float(row[int(options["coord-field-lat"]) - 1])
        lon = float(row[int(options["coord-field-lon"]) - 1])
        postcode = row[int(options["postcode-field"]) - 1]
        srid = int(options["srid"])
        location = Point(lon, lat, srid=srid)

        try:
            uprn = UPRN.objects.get(uprn=self.code)
            if (
                uprn.location[0] != location[0]
                or uprn.location[1] != location[1]
                or uprn.postcode != postcode
            ):
                uprn.location = location
                uprn.postcode = postcode
                uprn.save()
                self.count["updated"] += 1
            else:
                self.count["unchanged"] += 1
        except UPRN.DoesNotExist:
            uprn = UPRN.objects.create(
                uprn=self.code, location=location, postcode=postcode
            )
            self.count["created"] += 1
        for i, value in enumerate(row, start=1):
            uprn.codes.update_or_create(
                type=self.code_types[CODE_TYPE_MAP[i]], defaults={"code": str(value)}
            )
        self.count["total"] += 1
        if self.count["total"] % self.often == 0:
            self.print_stats()
        return uprn
