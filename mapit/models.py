import re
import itertools

from django.contrib.gis.db import models
from django.conf import settings
from django.db import connection
from django.db.models.query import RawQuerySet
from django.utils.encoding import python_2_unicode_compatible

from mapit import countries
from mapit.geometryserialiser import GeometrySerialiser


class GenerationManager(models.Manager):
    def current(self):
        """Return the most recent active generation.

        If there are no active generations, return 0."""

        latest_on = self.get_queryset().filter(active=True).order_by('-id')
        if latest_on:
            return latest_on[0]
        return 0

    def new(self):
        """If the most recent generation is inactive, return it.

        If there are no generations, or the most recent one is active,
        return None."""

        latest = self.get_queryset().order_by('-id')
        if not latest or latest[0].active:
            return None
        return latest[0]


@python_2_unicode_compatible
class Generation(models.Model):

    # Generations are used so that, theoretically, old versions of the same
    # data can be stored and accessed when new versions (ie. boundary changes
    # of some sort) come along. The current generation is the most recent
    # active generation, and is the default for e.g. postcode and point
    # lookups (both can be overridden to a different generation with a query
    # parameter). Inactive generations are so that you can load in new data
    # without it being returned by normal lookups by everyone using mapit.
    #
    # An Area in the database has a minimum and maximum generation that it is
    # valid for, so that you can see at which point an area was added and then
    # removed.
    #
    # As an example, http://mapit.mysociety.org/postcode/EH11BB.html is the
    # current areas for that postcode, whilst
    # http://mapit.mysociety.org/postcode/EH11BB.html?generation=14 gives you
    # the areas before the last Scottish Parliament boundary changes, hence
    # giving you the different areas involved.
    #
    # The concept works okay for boundary changes of things that have the
    # notion of being children - e.g. council wards, UK Parliament
    # constituencies, and so on - which are changed with a clean slate to a
    # new set (though note that if someone has some sort of alert on a ward
    # ID, that will stop at a point at which that ward ceases to exist, no
    # easy solution there). Where it falls down a bit is if the 'parent' has a
    # boundary change - users of mapit (including us) assume that e.g.
    # http://mapit.mysociety.org/area/2651.html is and always will be the City
    # of Edinburgh Council boundary. If the City of Edinburgh Council boundary
    # were to change, this should get a new ID starting at the new generation.
    # But that would break some things.
    #
    # Another example, as I've just fixed #32, is
    # http://mapit.mysociety.org/area/2253/children.html?type=UTW vs
    # http://mapit.mysociety.org/area/2253/children.html?generation=14;type=UTW
    # - the wards of Bedford before and after a boundary change.

    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    description = models.CharField(
        max_length=255, help_text="Describe this generation, eg '2010 electoral boundaries'")

    objects = GenerationManager()

    class Meta:
        ordering = ('id',)

    def __str__(self):
        id = self.id or '?'
        return "Generation %s (%sactive)" % (id, "" if self.active else "in")

    def as_dict(self):
        return {
            'id': self.id,
            'active': self.active,
            'created': self.created,
            'description': self.description,
        }


@python_2_unicode_compatible
class Country(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'countries'


@python_2_unicode_compatible
class Type(models.Model):

    # An area type (the Type model) is the type of area. You can see examples
    # for a few countries in the mapit/fixtures directory. In the UK we have
    # county councils (CTY), district councils (DIS), constituencies of the UK
    # Parliament (WMC), Scottish Parliament regions (SPE), and so on. The fact
    # these examples are three letter codes is a hangover from the original
    # source data we used from Ordnance Survey.

    code = models.CharField(max_length=500, unique=True, help_text="A unique code, eg 'CTR', 'CON', etc")
    description = models.CharField(
        max_length=200, blank=True, help_text="The name of the type of area, eg 'Country', 'Constituency', etc")

    def __str__(self):
        return '%s (%s)' % (self.description, self.code)


class AreaManager(models.GeoManager):
    def get_queryset(self):
        return super(AreaManager, self).get_queryset().select_related('type', 'country')

    def by_location(self, location, generation=None):
        if generation is None:
            generation = Generation.objects.current()
        if not location:
            return []
        return Area.objects.filter(
            polygons__polygon__contains=location,
            generation_low__lte=generation, generation_high__gte=generation
        )

    def by_postcode(self, postcode, generation=None):
        if not generation:
            generation = Generation.objects.current()
        return list(itertools.chain(
            self.by_location(postcode.location, generation),
            postcode.areas.filter(
                generation_low__lte=generation, generation_high__gte=generation
            )
        ))

    # In order for this query to be performant, we have to do it ourselves.
    # We force the non-geographical part of the query to be done first, because
    # if a type is specified, that greatly speeds it up.
    def intersect(self, query_type, area, types, generation):
        if not isinstance(query_type, list):
            query_type = [query_type]

        params = [area.id, area.id, generation.id, generation.id]

        if types:
            params.append(tuple(types))
            query_area_type = ' AND mapit_area.type_id IN (SELECT id FROM mapit_type WHERE code IN %s) '
        else:
            query_area_type = ''

        query_geo = ' OR '.join(['ST_%s(geometry.polygon, target.polygon)' % type for type in query_type])

        query = '''
WITH
    target AS ( SELECT ST_collect(polygon) polygon FROM mapit_geometry WHERE area_id=%%s ),
    geometry AS (
        SELECT mapit_geometry.*
          FROM mapit_geometry, mapit_area, target
         WHERE mapit_geometry.area_id = mapit_area.id
               AND mapit_geometry.polygon && target.polygon
               AND mapit_area.id != %%s
               AND mapit_area.generation_low_id <= %%s
               AND mapit_area.generation_high_id >= %%s
               %s
    )
SELECT DISTINCT mapit_area.*
  FROM mapit_area, geometry, target
 WHERE geometry.area_id = mapit_area.id AND (%s)
''' % (query_area_type, query_geo)
        return RawQuerySet(raw_query=query, model=self.model, params=params, using=self._db)

    def get_or_create_with_name(self, country=None, type=None, name_type='', name=''):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        area, created = Area.objects.get_or_create(
            country=country, type=type,
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            names__type__code=name_type, names__name=name,
            defaults={'generation_low': new_generation, 'generation_high': new_generation}
        )
        if created:
            area.names.get_or_create(type=NameType.objects.get(code=name_type), name=name)
        else:
            area.generation_high = new_generation
            area.save()
        return area

    def get_or_create_with_code(self, country=None, type=None, code_type='', code=''):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        area, created = Area.objects.get_or_create(
            country=country, type=type,
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            codes__type__code=code_type, codes__code=code,
            defaults={'generation_low': new_generation, 'generation_high': new_generation}
        )
        if created:
            area.codes.get_or_create(type=CodeType.objects.get(code=code_type), code=code)
        else:
            area.generation_high = new_generation
            area.save()
        return area


@python_2_unicode_compatible
class Area(models.Model):
    name = models.CharField(max_length=2000, blank=True)
    parent_area = models.ForeignKey('self', related_name='children', null=True, blank=True, on_delete=models.CASCADE)
    type = models.ForeignKey(Type, related_name='areas', on_delete=models.CASCADE)
    country = models.ForeignKey(Country, related_name='areas', null=True, blank=True, on_delete=models.CASCADE)
    generation_low = models.ForeignKey(Generation, related_name='new_areas', null=True, on_delete=models.CASCADE)
    generation_high = models.ForeignKey(Generation, related_name='final_areas', null=True, on_delete=models.CASCADE)

    objects = AreaManager()

    class Meta:
        ordering = ('name', 'type')

    @property
    def all_codes(self):
        if not hasattr(self, '_all_codes'):
            code_list = self.codes.select_related('type')
            self._all_codes = {}
            for code in code_list:
                self._all_codes[code.type.code] = code.code
        return self._all_codes

    @all_codes.setter
    def all_codes(self, value):
        self._all_codes = value

    def __str__(self):
        name = self.name or '(unknown)'
        return '%s %s' % (self.type.code, name)

    def as_dict(self, all_names=None):
        all_names = all_names or []
        return {
            'id': self.id,
            'name': self.name,
            'parent_area': self.parent_area_id,
            'type': self.type.code,
            'type_name': self.type.description,
            'country': self.country.code if self.country else '',
            'country_name': self.country.name if self.country else '-',
            'generation_low': self.generation_low_id,
            'generation_high': self.generation_high_id,
            'codes': self.all_codes,
            'all_names': dict(n.as_tuple() for n in all_names),
        }

    def css_indent_class(self):
        """Get a CSS class for use on <li> representations of this area

        Currently this is only used to indicate the indentation level
        that should be used on the code types O02, O03, O04 ... O011,
        which are only used by global MapIt.
        """
        m = re.search(r'^O([01][0-9])$', self.type.code)
        if m:
            level = int(m.group(1), 10)
            return "area_level_%d" % (level,)
        else:
            return ""

    def export(self,
               srid,
               export_format,
               simplify_tolerance=0,
               line_colour="70ff0000",
               fill_colour="3dff5500",
               kml_type="full"):
        """Generate a representation of the area in KML, GeoJSON or WKT

        This returns a tuple of (data, content_type), which are
        strings representing the data itself and its MIME type.  If
        there are no polygons associated with this area (None, None)
        is returned.  'export_format' may be one of 'kml', 'wkt,
        'json' and 'geojson', the last two being synonymous.  The
        'srid' parameter specifies the coordinate system that the
        polygons should be transformed into before being exported, if
        it is different from this MapIt.  simplify_tolerance, if
        non-zero, is passed to
        django.contrib.gis.geos.GEOSGeometry.simplify for simplifying
        the polygon boundary before export.  The line_colour and
        fill_colour parameters are only used if the export type is KML
        and kml_type is 'full'.  The 'kml_type' parameter may be
        either 'full' (in which case a complete, valid KML file is
        returned) or 'polygon' (in which case just the <Polygon>
        element is returned).

        If the simplify_tolerance provided is large enough that all
        the polygons completely disappear under simplification, or
        something else goes wrong with the spatial transform, then a
        TransformError exception is raised.
        """
        all_polygons = self.polygons.all()
        if len(all_polygons) == 0:
            return (None, None)
        serialiser = GeometrySerialiser(self, srid, simplify_tolerance)
        if export_format == 'kml':
            out, content_type = serialiser.kml(kml_type, line_colour, fill_colour)
        elif export_format in ('json', 'geojson'):
            out, content_type = serialiser.geojson()
        elif export_format == 'wkt':
            out, content_type = serialiser.wkt()
        return (out, content_type)


@python_2_unicode_compatible
class Geometry(models.Model):
    area = models.ForeignKey(Area, related_name='polygons', on_delete=models.CASCADE)
    polygon = models.PolygonField(srid=settings.MAPIT_AREA_SRID)
    objects = models.GeoManager()

    class Meta:
        verbose_name_plural = 'geometries'

    def __str__(self):
        return '%s, polygon %d' % (self.area, self.id)


@python_2_unicode_compatible
class NameType(models.Model):

    # Name types are for storing different types of names. This could have
    # different uses - in the UK it is used to store names from different
    # sources, and then one is picked for the canonical name on the Area model
    # itself; in global MaPit, the different language names are stored here
    # and displayed in the alternative names section.

    code = models.CharField(
        max_length=10, unique=True, help_text="A unique code to identify this type of name: eg 'english' or 'iso'")
    description = models.CharField(
        max_length=200, blank=True, help_text="The name of this type of name, eg 'English' or 'ISO Standard'")
    objects = models.Manager()

    def __str__(self):
        return '%s (%s)' % (self.description, self.code)


@python_2_unicode_compatible
class Name(models.Model):
    area = models.ForeignKey(Area, related_name='names', on_delete=models.CASCADE)
    type = models.ForeignKey(NameType, related_name='names', on_delete=models.CASCADE)
    name = models.CharField(max_length=2000)
    objects = models.Manager()

    class Meta:
        unique_together = ('area', 'type')

    def __str__(self):
        return '%s (%s) [%s]' % (self.name, self.type.code, self.area.id)

    def save(self, *args, **kwargs):
        super(Name, self).save(*args, **kwargs)
        if hasattr(countries, 'name_save_hook'):
            countries.name_save_hook(self)

    def as_tuple(self):
        return (self.type.code, [self.type.description, self.name])


@python_2_unicode_compatible
class CodeType(models.Model):

    # Code types are so you can store different types of code for an area. In
    # the UK we have "ons" for old style Office of National Statistics codes,
    # "gss" for new style ONS codes, and unit_id for the Ordnance Survey ID.
    # This could be extended to a more generic data store of information on an
    # object, perhaps.

    code = models.CharField(max_length=10, unique=True, help_text="A unique code, eg 'ons' or 'unit_id'")
    description = models.CharField(
        max_length=200, blank=True,
        help_text="The name of the code, eg 'Office of National Statitics' or 'Ordnance Survey ID'")

    def __str__(self):
        return '%s (%s)' % (self.description, self.code)


@python_2_unicode_compatible
class Code(models.Model):
    area = models.ForeignKey(Area, related_name='codes', on_delete=models.CASCADE)
    type = models.ForeignKey(CodeType, related_name='codes', on_delete=models.CASCADE)
    code = models.CharField(max_length=500)
    objects = models.Manager()

    class Meta:
        unique_together = ('area', 'type')

    def __str__(self):
        return '%s (%s) [%s]' % (self.code, self.type.code, self.area.id)


# Postcodes

class PostcodeQuerySet(models.query.GeoQuerySet):
    # ST_CoveredBy on its own does not appear to use the index.
    # Plus this way we can keep the polygons in the database
    # without pulling out in a giant WKB string
    def filter_by_area(self, area):
        collect = '''ST_Transform((select ST_Collect(polygon) from mapit_geometry
            where area_id=%s group by area_id), 4326)'''
        return self.extra(
            where=[
                'location && %s' % collect,
                'ST_CoveredBy(location, %s)' % collect
            ],
            params=[area.id, area.id]
        )


@python_2_unicode_compatible
class Postcode(models.Model):
    postcode = models.CharField(max_length=7, db_index=True, unique=True)
    location = models.PointField(null=True)
    # Will hopefully use PostGIS point-in-polygon tests, but if we don't have the polygons...
    areas = models.ManyToManyField(Area, related_name='postcodes', blank=True)

    objects = PostcodeQuerySet.as_manager()

    class Meta:
        ordering = ('postcode',)

    def __str__(self):
        return self.get_postcode_display()

    # Prettify postcode for display, if we know how to
    def get_postcode_display(self):
        if hasattr(countries, 'get_postcode_display'):
            return countries.get_postcode_display(self.postcode)
        return self.postcode

    def as_dict(self):
        if not self.location:
            return {
                'postcode': self.get_postcode_display(),
            }
        loc = self.location
        result = {
            'postcode': self.get_postcode_display(),
            'wgs84_lon': loc[0],
            'wgs84_lat': loc[1]
        }
        if hasattr(countries, 'augment_postcode'):
            countries.augment_postcode(self, result)
        return result

    # Doing this via self.location.transform(29902) gives incorrect results.
    # The database has the right proj4 text, the proj file does not. I think.
    def as_irish_grid(self):
        cursor = connection.cursor()
        cursor.execute("SELECT ST_AsText(ST_Transform(ST_GeomFromText('POINT(%f %f)', 4326), 29902))" % (
            self.location[0], self.location[1]))
        row = cursor.fetchone()
        m = re.match('POINT\((.*?) (.*)\)', row[0])
        return list(map(float, m.groups()))
