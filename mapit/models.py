import re
import itertools

from django.contrib.gis.db import models
from django.conf import settings
from django.db import connection

from mapit.managers import Manager, GeoManager
from mapit import countries

class GenerationManager(models.Manager):
    def current(self):
        """Return the most recent active generation.

        If there are no active generations, return 0."""

        latest_on = self.get_query_set().filter(active=True).order_by('-id')
        if latest_on: return latest_on[0]
        return 0

    def new(self):
        """If the most recent generation is inactive, return it.

        If there are no generations, or the most recent one is active,
        return None."""

        latest = self.get_query_set().order_by('-id')
        if not latest or latest[0].active:
            return None
        return latest[0]
        
class Generation(models.Model):
    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=255)

    objects = GenerationManager()

    def __unicode__(self):
        id = self.id or '?'
        return "Generation %s (%sactive)" % (id, "" if self.active else "in")

    def as_dict(self):
        return {
            'id': self.id,
            'active': self.active,
            'created': self.created,
            'description': self.description,
        }

class Country(models.Model):
    code = models.CharField(max_length=1, unique=True)
    name = models.CharField(max_length=100, unique=True)

    def __unicode__(self):
        return self.name
    
    class Meta:
        verbose_name_plural='countries'

class Type(models.Model):
    code = models.CharField(max_length=3, unique=True)
    description = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return '%s (%s)' % (self.description, self.code)

class AreaManager(models.GeoManager):
    def by_location(self, location, generation=None):
        if generation is None: generation = Generation.objects.current()
        if not location: return []
        #return Area.objects.filter(
        #    polygons__polygon__contains=location,
        #    generation_low__lte=generation, generation_high__gte=generation
        #)
	# XXX The above is what I would like to use, and have used until now;
	# However when run with generation 15 (loaded today, which contains
	# nothing but the 2011 Scottish Parliament boundaries), postgres uses
	# up all available memory on the machine and cries, which has never
	# happened before. Here are the two EXPLAINs, first the one that works
	# fine:
        # 
        # mapit=> explain SELECT "areas_area"."id", "areas_area"."name", "areas_area"."parent_area_id", "areas_area"."type", "areas_area"."country", "areas_area"."generation_low_id", "areas_area"."generation_high_id" FROM "areas_area" INNER JOIN "areas_geometry" ON ("areas_area"."id" = "areas_geometry"."area_id") WHERE (ST_Contains("areas_geometry"."polygon", ST_Transform(ST_GeomFromWKB('\\001\\001\\000\\000\\000\\250\\012v\\232\\001\\205\\011\\300F\\365V\\357\\331\\371K@', 4326), 27700)) AND "areas_area"."generation_low_id" <= 14  AND "areas_area"."generation_high_id" >= 14 ) ORDER BY "areas_area"."name" ASC, "areas_area"."type" ASC ;
        #  Sort  (cost=16.64..16.65 rows=1 width=37)
        #    Sort Key: areas_area.name, areas_area.type
        #    ->  Nested Loop  (cost=0.00..16.63 rows=1 width=37)
        #          ->  Index Scan using areas_geometry_polygon_id on areas_geometry  (cost=0.00..8.31 rows=1 width=4)
        #                Index Cond: (polygon && '0101000020346C0000E85CCE0080E213417E2EF7FF7B902441'::geometry)
        #                Filter: ((polygon && '0101000020346C0000E85CCE0080E213417E2EF7FF7B902441'::geometry) AND _st_contains(polygon, '0101000020346C0000E85CCE0080E213417E2EF7FF7B902441'::geometry))
        #          ->  Index Scan using areas_area_pkey on areas_area  (cost=0.00..8.31 rows=1 width=37)
        #                Index Cond: (areas_area.id = areas_geometry.area_id)
        #                Filter: ((areas_area.generation_low_id <= 14) AND (areas_area.generation_high_id >= 14))
        # (9 rows)
        # 
        # And the identical query but with a different generation ID that kills the server:
        #
        # mapit=> explain SELECT "areas_area"."id", "areas_area"."name", "areas_area"."parent_area_id", "areas_area"."type", "areas_area"."country", "areas_area"."generation_low_id", "areas_area"."generation_high_id" FROM "areas_area" INNER JOIN "areas_geometry" ON ("areas_area"."id" = "areas_geometry"."area_id") WHERE (ST_Contains("areas_geometry"."polygon", ST_Transform(ST_GeomFromWKB('\\001\\001\\000\\000\\000\\250\\012v\\232\\001\\205\\011\\300F\\365V\\357\\331\\371K@', 4326), 27700)) AND "areas_area"."generation_low_id" <= 15  AND "areas_area"."generation_high_id" >= 15 ) ORDER BY "areas_area"."name" ASC, "areas_area"."type" ASC ;
        #  Sort  (cost=16.63..16.64 rows=1 width=37)
        #    Sort Key: areas_area.name, areas_area.type
        #    ->  Nested Loop  (cost=0.00..16.62 rows=1 width=37)
        #          Join Filter: (areas_area.id = areas_geometry.area_id)
        #          ->  Index Scan using areas_area_generation_high_id on areas_area  (cost=0.00..8.30 rows=1 width=37)
        #                Index Cond: (generation_high_id >= 15)
        #                Filter: (generation_low_id <= 15)
        #          ->  Index Scan using areas_geometry_polygon_id on areas_geometry  (cost=0.00..8.31 rows=1 width=4)
        #                Index Cond: (areas_geometry.polygon && '0101000020346C0000E85CCE0080E213417E2EF7FF7B902441'::geometry)
        #                Filter: ((areas_geometry.polygon && '0101000020346C0000E85CCE0080E213417E2EF7FF7B902441'::geometry) AND _st_contains(areas_geometry.polygon, '0101000020346C0000E85CCE0080E213417E2EF7FF7B902441'::geometry))
        # (10 rows)
        #
	# I have no idea why the latter seems to mean it needs to load the
	# shapes into memory, but it does, it's 1am on a Saturday, and so I
	# really don't want to think about it. So instead, let's do the query
	# planner's job for it and first do the Geometry contains lookup, and
	# then fetch just the Areas that are in the right generation(s).
        # At least Like A Prayer is on. XXX

        # list() to force evaluation here, we don't want it as a subquery
        geoms = list(Geometry.objects.filter(polygon__contains=location).defer('polygon'))
        return Area.objects.filter(
            polygons__in=geoms,
            generation_low__lte=generation, generation_high__gte=generation
        )

    def by_postcode(self, postcode, generation=None):
        if not generation: generation = Generation.objects.current()
        return list(itertools.chain(
            self.by_location(postcode.location, generation),
            postcode.areas.filter(
                generation_low__lte=generation, generation_high__gte=generation
            )
        ))

    def intersect(self, query_type, area):
        if not isinstance(query_type, list): query_type = [ query_type ]

        where = [
            'mapit_geometry.area_id = mapit_area.id',
            'mapit_geometry.polygon && (select st_collect(polygon) from mapit_geometry where area_id=%s)',
        ]
        where.append('(' + ' OR '.join([ 'ST_%s(mapit_geometry.polygon, (select st_collect(polygon) from mapit_geometry where area_id=%%s))' % type for type in query_type ]) + ')')

        return Area.objects.exclude(id=area.id).extra(
            tables = [ 'mapit_geometry' ],
            where = where,
            params = [ area.id ] * ( 1 + len(query_type) ),
        )

    def get_or_create_with_name(self, country=None, type=None, name_type='', name=''):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        area, created = Area.objects.get_or_create(country=country, type=type,
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            names__type__code=name_type, names__name=name,
            defaults = { 'generation_low': new_generation, 'generation_high': new_generation }
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
        area, created = Area.objects.get_or_create(country=country, type=type,
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            codes__type__code=code_type, codes__code=code,
            defaults = { 'generation_low': new_generation, 'generation_high': new_generation }
        )
        if created:
            area.codes.get_or_create(type=CodeType.objects.get(code=code_type), code=code)
        else:
            area.generation_high = new_generation
            area.save()
        return area

class Area(models.Model):
    name = models.CharField(max_length=100, editable=False, blank=True) # Automatically set from name children
    parent_area = models.ForeignKey('self', related_name='children', null=True, blank=True)
    type = models.ForeignKey(Type, related_name='areas')
    country = models.ForeignKey(Country, related_name='areas', null=True, blank=True)
    generation_low = models.ForeignKey(Generation, related_name='new_areas', null=True)
    generation_high = models.ForeignKey(Generation, related_name='final_areas', null=True)

    objects = AreaManager()

    class Meta:
        ordering = ('name', 'type')

    @property
    def all_codes(self):
        if not getattr(self, 'code_list', None):
            self.code_list = self.codes.all()
        codes = {}
        for code in self.code_list:
            codes[code.type.code] = code.code
        return codes

    def __unicode__(self):
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

    def css_class(self):
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

class Geometry(models.Model):
    area = models.ForeignKey(Area, related_name='polygons')
    polygon = models.PolygonField(srid=settings.MAPIT_AREA_SRID)
    objects = GeoManager()

    class Meta:
        verbose_name_plural = 'geometries'

    def __unicode__(self):
        return u'%s, polygon %d' % (self.area, self.id)

class NameType(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=200, blank=True)
    objects = Manager()

    def __unicode__(self):
        return '%s (%s)' % (self.description, self.code)

class Name(models.Model):
    area = models.ForeignKey(Area, related_name='names')
    type = models.ForeignKey(NameType, related_name='names')
    name = models.CharField(max_length=100)
    objects = Manager()

    class Meta:
        unique_together = ('area', 'type')

    def __unicode__(self):
        return '%s (%s) [%s]' % (self.name, self.type.code, self.area.id)

    def make_friendly_name(self, name):
        n = re.sub('\s+', ' ', name.name.strip())
        n = n.replace('St. ', 'St ')
        if name.type.code == 'M': return n
        if name.type.code == 'S': return n
        # Type must be 'O' here
        n = re.sub(' Euro Region$', '', n) # EUR
        n = re.sub(' (Burgh|Co|Boro) Const$', '', n) # WMC
        n = re.sub(' P Const$', '', n) # SPC
        n = re.sub(' PER$', '', n) # SPE
        n = re.sub(' GL Assembly Const$', '', n) # LAC
        n = re.sub(' Assembly Const$', '', n) # WAC
        n = re.sub(' Assembly ER$', '', n) # WAE
        n = re.sub(' London Boro$', ' Borough', n) # LBO
        if self.area.country and self.area.country.name == 'Wales': n = re.sub('^.*? - ', '', n) # UTA
        n = re.sub('(?:The )?City of (.*?) (District )?\(B\)$', r'\1 City', n) # UTA
        n = re.sub(' District \(B\)$', ' Borough', n) # DIS
        n = re.sub(' \(B\)$', ' Borough', n) # DIS
        if self.area.type.code in ('CTY', 'DIS', 'LBO', 'UTA', 'MTD'): n += ' Council'
        n = re.sub(' (ED|CP)$', '', n) # CPC, CED, UTE
        n = re.sub(' Ward$', '', n) # DIW, LBW, MTW, UTW
        return n

    def save(self, *args, **kwargs):
        super(Name, self).save(*args, **kwargs)
        try:
            name = self.area.names.filter(type__code__in=('M', 'O', 'S')).order_by('type__code')[0]
            self.area.name = self.make_friendly_name(name)
            self.area.save()
        except:
            pass

    def as_tuple(self):
        return (self.type.code, [self.type.description,
                                 self.name])

class CodeType(models.Model):
    code = models.CharField(max_length=10, unique=True)
    description = models.CharField(max_length=200, blank=True)

    def __unicode__(self):
        return '%s (%s)' % (self.description, self.code)

class Code(models.Model):
    area = models.ForeignKey(Area, related_name='codes')
    type = models.ForeignKey(CodeType, related_name='codes')
    code = models.CharField(max_length=10)
    objects = Manager()

    class Meta:
        unique_together = ('area', 'type')

    def __unicode__(self):
        return '%s (%s) [%s]' % (self.code, self.type.code, self.area.id)

# Postcodes

class PostcodeManager(GeoManager):
    def get_query_set(self):
        return self.model.QuerySet(self.model)
    def __getattr__(self, attr, *args):
        return getattr(self.get_query_set(), attr, *args)

class Postcode(models.Model):
    postcode = models.CharField(max_length=7, db_index=True, unique=True)
    location = models.PointField(null=True)
    # Will hopefully use PostGIS point-in-polygon tests, but if we don't have the polygons...
    areas = models.ManyToManyField(Area, related_name='postcodes', blank=True)

    objects = PostcodeManager()

    class Meta:
        ordering = ('postcode',)

    class QuerySet(models.query.GeoQuerySet):
        # ST_CoveredBy on its own does not appear to use the index.
        # Plus this way we can keep the polygons in the database
        # without pulling out in a giant WKB string
        def filter_by_area(self, area):
            collect = 'ST_Transform((select ST_Collect(polygon) from mapit_geometry where area_id=%s group by area_id), 4326)'
            return self.extra(
                where = [
                    'location && %s' % collect,
                    'ST_CoveredBy(location, %s)' % collect
                ],
                params = [ area.id, area.id ]
            )

    def __unicode__(self):
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
        cursor.execute("SELECT ST_AsText(ST_Transform(ST_GeomFromText('POINT(%f %f)', 4326), 29902))" % (self.location[0], self.location[1]))
        row = cursor.fetchone()
        m = re.match('POINT\((.*?) (.*)\)', row[0])
        return map(float, m.groups())

