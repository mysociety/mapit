import itertools

from django.shortcuts import render
from mapit.shortcuts import output_json, get_object_or_404

from mapit_labour.models import UPRN
from mapit.models import Generation, Area
from mapit.views.postcodes import add_codes, enclosing_areas
from mapit.middleware import ViewException

# Create your views here.


def uprn(request, uprn, format="json"):
    uprn = get_object_or_404(UPRN, format=format, uprn=uprn)

    try:
        generation = int(request.GET["generation"])
    except:
        generation = Generation.objects.current()
    areas = list(add_codes(Area.objects.by_location(uprn.location, generation)))

    shortcuts = {}
    for area in areas:
        if area.type.code in ("COP", "LBW", "LGE", "MTW", "UTE", "UTW"):
            shortcuts["ward"] = area.id
            shortcuts["council"] = area.parent_area_id
        elif area.type.code == "CED":
            shortcuts.setdefault("ward", {})["county"] = area.id
            shortcuts.setdefault("council", {})["county"] = area.parent_area_id
        elif area.type.code == "DIW":
            shortcuts.setdefault("ward", {})["district"] = area.id
            shortcuts.setdefault("council", {})["district"] = area.parent_area_id
        elif area.type.code in ("WMC",):
            # XXX Also maybe 'EUR', 'NIE', 'SPC', 'SPE', 'WAC', 'WAE', 'OLF', 'OLG', 'OMF', 'OMG'):
            shortcuts[area.type.code] = area.id

    # Add manual enclosing areas.
    extra = []
    for area in areas:
        if area.type.code in enclosing_areas.keys():
            extra.extend(enclosing_areas[area.type.code])
    areas = itertools.chain(areas, Area.objects.filter(id__in=extra))

    if format == "html":
        return render(
            request,
            "mapit_labour/uprn.html",
            {
                "uprn": uprn.as_dict(),
                "areas": areas,
                "json_view": "mapit_labour-uprn",
            },
        )

    out = uprn.as_dict()
    out["areas"] = dict((area.id, area.as_dict()) for area in areas)

    if shortcuts:
        out["shortcuts"] = shortcuts
    return output_json(out, include_debug_db_queries=False)


def addressbase(request):
    if not request.GET:
        raise ViewException(
            "json",
            "At least one AddressBase Core field should be specified in the query parameters.",
            400,
        )

    uprns = UPRN.objects.all()
    for code, value in request.GET.items():
        uprns = uprns.filter(codes__type__code__iexact=code, codes__code__iexact=value)

    return output_json([uprn.as_dict()["addressbase_core"] for uprn in uprns[:10]])
