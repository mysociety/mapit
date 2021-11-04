from mapit.management.commands.mapit_import_postal_codes import Command

from django.contrib.gis.geos import Point

from mapit_labour.models import UPRN


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
        self.count["total"] += 1
        if self.count["total"] % self.often == 0:
            self.print_stats()
        return uprn
