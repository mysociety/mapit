# This command is used to add GSS codes to existing CED areas in the DB, using
# data an ONS CED boundary file, e.g. the GeoPackage from
# https://geoportal.statistics.gov.uk/datasets/county-electoral-division-may-2026-boundaries-en-bgc
#
# Boundary-Line CED areasd don't include a GSS code for some reason, so we
# compare polygons in the ONS GPKG with those in our DB for the best spatial
# match, and assign the GSS code accordingly.

import re

from django.conf import settings
from django.contrib.gis.gdal import DataSource
from django.core.management.base import LabelCommand, CommandError
from django.db import transaction

from mapit.models import Area, Generation, CodeType

# How much spatial overlap is required (0-1) before we accept it as a match.
MIN_OVERLAP = 0.9


class Command(LabelCommand):
    help = "Adds GSS codes to CED areas from an ONS CED boundary geopackage"
    label = "<ONS CED boundary .gpkg>"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--commit",
            action="store_true",
            dest="commit",
            help="Commit changes to database",
        )
        parser.add_argument(
            "--generation",
            dest="generation",
            type=int,
            help="Generation to search for CED areas in (default: current)",
        )

    @transaction.atomic
    def handle_label(self, filename, **options):
        generation = options["generation"] or Generation.objects.current()
        if not generation:
            raise CommandError("No active generation, and no --generation given")
        gss = CodeType.objects.get(code="gss")

        layer = DataSource(filename)[0]
        code_field, name_field = self._get_ons_fields(layer)

        matched = {}
        for feat in layer:
            geometry = feat.geom.geos
            if geometry.srid != settings.MAPIT_AREA_SRID:
                geometry.transform(settings.MAPIT_AREA_SRID)
            ons_code, ons_name = feat[code_field].value, feat[name_field].value

            area = self._best_match(geometry, generation)
            if area is None:
                raise CommandError(f"No CED Area overlaps {ons_name} ({ons_code}) by at least {MIN_OVERLAP:.0%}")
            if area.id in matched:  # we've already found a match for this CED Area, bail out
                raise CommandError(f"{area.name} matches both {matched[area.id]} and {ons_code}")
            matched[area.id] = ons_code

            area.codes.update_or_create(type=gss, defaults={"code": ons_code})
            self.stdout.write(f"{area.name}: {ons_code}")

        for area in self._get_ced_areas(generation).exclude(id__in=matched.keys()):
            self.stderr.write(f"Warning: no ONS CED matched {area.name} [{area.id}]")

        if not options["commit"]:
            transaction.set_rollback(True)

    def _get_ons_fields(self, layer):
        codes = [f for f in layer.fields if re.match(r"CED\d\dCD$", f)]
        names = [f for f in layer.fields if re.match(r"CED\d\dNM$", f)]
        if len(codes) != 1 or len(names) != 1:
            raise CommandError(f"CEDyyCD and CEDyyNM fields not found in {layer.fields}")
        return codes[0], names[0]

    def _get_ced_areas(self, generation):
        return Area.objects.filter(
            type__code="CED",
            generation_low__lte=generation,
            generation_high__gte=generation,
        )

    def _best_match(self, geometry, generation):
        """Return the existing CED Area whose polygons overlap geometry the most, or None if MIN_OVERLAP isn't met."""
        candidates = self._get_ced_areas(generation).filter(polygons__polygon__intersects=geometry).distinct()
        best, best_overlap = None, 0
        for area in candidates:
            overlap = sum(p.polygon.intersection(geometry).area for p in area.polygons.all())
            if overlap > best_overlap:
                best, best_overlap = area, overlap
        if best_overlap < MIN_OVERLAP * geometry.area:
            return None
        return best
