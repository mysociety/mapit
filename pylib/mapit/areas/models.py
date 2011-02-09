import re
import itertools
from django.contrib.gis.db import models
from mapit.managers import Manager, GeoManager
import mysociety.config

class GenerationManager(models.Manager):
    def current(self):
        latest_on = self.get_query_set().filter(active=True).order_by('-id')
        if latest_on: return latest_on[0]
        return 0

    def new(self):
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
        return Area.objects.exclude(id=area.id).extra(
            tables = [ 'areas_geometry' ],
            where = [ 'areas_geometry.area_id = areas_area.id', 'ST_%s(areas_geometry.polygon, (select polygon from areas_geometry where area_id=%%s))' % query_type ],
            params = [area.id]
        )

    def get_or_create_with_name(self, country='', type='', name_type='', name=''):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        area, created = Area.objects.get_or_create(country=country, type=type,
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            names__type=name_type, names__name=name,
            defaults = { 'generation_low': new_generation, 'generation_high': new_generation }
        )
        if created:
            area.names.get_or_create(type=name_type, name=name)
        else:
            area.generation_high = new_generation
            area.save()
        return area

    def get_or_create_with_code(self, country='', type='', code_type='', code=''):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        area, created = Area.objects.get_or_create(country=country, type=type,
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            codes__type=code_type, codes__code=code,
            defaults = { 'generation_low': new_generation, 'generation_high': new_generation }
        )
        if created:
            area.codes.get_or_create(type=code_type, code=code)
        else:
            area.generation_high = new_generation
            area.save()
        return area

class Area(models.Model):
    name = models.CharField(max_length=100, editable=False, blank=True) # Automatically set from name children
    parent_area = models.ForeignKey('self', related_name='children', null=True, blank=True)
    type = models.CharField(max_length=3, db_index=True, choices=(
        ('EUP', 'European Parliament'),
        ('EUR', 'European region'),
        ('HOL', 'House of Lords'),
        ('HOC', 'House of Lords constituency'),
        ('WMP', 'UK Parliament'),
        ('WMC', 'UK Parliament constituency'),
        ('Northern Ireland', (
            ('NIA', 'Northern Ireland Assembly'),
            ('NIE', 'Northern Ireland Assembly constituency'),
            ('LGD', 'Northern Irish Council'),
            ('LGE', 'Northern Irish Council electoral area'),
            ('LGW', 'Northern Irish Council ward'),
        )),
        ('England', (
            ('CTY', 'County council'),
            ('CED', 'County council ward'),
            ('DIS', 'District council'),
            ('DIW', 'District council ward'),
            ('GLA', 'Greater London Authority'),
            ('LAC', 'London Assembly constituency'),
            ('LAE', 'London Assembly area (shared)'),
            ('LAS', 'London Assembly area'),
            ('LBO', 'London borough'),
            ('LBW', 'London borough ward'),
            ('MTD', 'Metropolitan district'),
            ('MTW', 'Metropolitan district ward'),
            ('COI', 'Scilly Isles'),
            ('COP', 'Scilly Isles "ward"'),
        )),
        ('SPA', 'Scottish Parliament'),
        ('SPC', 'Scottish Parliament constituency'),
        ('SPE', 'Scottish Parliament region'),
        ('WAS', 'Welsh Assembly'),
        ('WAC', 'Welsh Assembly constituency'),
        ('WAE', 'Welsh Assembly region'),
        ('UTA', 'Unitary Authority'),
        ('UTE', 'Unitary Authority ward (UTE)'),
        ('UTW', 'Unitary Authority ward (UTW)'),
        ('England and Wales', (
            ('CPC', 'Civil Parish'),
            ('OLF', 'Lower Layer Super Output Area (Full)'),
            ('OLG', 'Lower Layer Super Output Area (Generalised)'),
            ('OMF', 'Middle Layer Super Output Area (Full)'),
            ('OMG', 'Middle Layer Super Output Area (Generalised)'),
        )),
        ('Norway', (
            ('NKO', 'Norway Kommune'),
        )),
    ))
    country = models.CharField(max_length=1, choices=(
        ('E', 'England'),
        ('W', 'Wales'),
        ('S', 'Scotland'),
        ('N', 'Northern Ireland'),
        ('O', 'Norway'),
        ('', '-'),
    ), blank=True)
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
            codes[code.type] = code.code
        return codes

    def __unicode__(self):
        name = self.name or '(unknown)'
        return '%s %s' % (self.type, name)

    def as_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'parent_area': self.parent_area_id,
            'type': self.type,
            'type_name': self.get_type_display(),
            'country': self.country,
            'country_name': self.get_country_display(),
            'generation_low': self.generation_low_id,
            'generation_high': self.generation_high_id,
            'codes': self.all_codes,
        }

class Geometry(models.Model):
    area = models.ForeignKey(Area, related_name='polygons')
    polygon = models.PolygonField(srid=int(mysociety.config.get('AREA_SRID')))
    objects = GeoManager()

    class Meta:
        verbose_name_plural = 'geometries'

    def __unicode__(self):
        return u'%s, polygon %d' % (self.area, self.id)

class Name(models.Model):
    area = models.ForeignKey(Area, related_name='names')
    type = models.CharField(max_length=1, choices=(
        ('O', 'Ordnance Survey'),
        ('S', 'ONS (SNAC/GSS)'),
        ('M', 'Override name'),
    ))
    name = models.CharField(max_length=100)
    objects = Manager()

    class Meta:
        unique_together = ('area', 'type')

    def __unicode__(self):
        return '%s (%s) [%s]' % (self.name, self.type, self.area.id)

    def make_friendly_name(self, name):
        n = re.sub('\s+', ' ', name.name.strip())
        n = n.replace('St. ', 'St ')
        if name.type == 'M': return n
        if name.type == 'S': return n
        # Type must be 'O' here
        n = re.sub(' Euro Region$', '', n) # EUR
        n = re.sub(' (Burgh|Co|Boro) Const$', '', n) # WMC
        n = re.sub(' (Islands )?P Const$', '', n) # SPC
        n = re.sub(' PER$', '', n) # SPE
        n = re.sub(' GL Assembly Const$', '', n) # LAC
        n = re.sub(' Assembly Const$', '', n) # WAC
        n = re.sub(' Assembly ER$', '', n) # WAE
        n = re.sub(' London Boro$', ' Borough', n) # LBO
        if self.area.country == 'W': n = re.sub('^.*? - ', '', n) # UTA
        n = re.sub('(?:The )?City of (.*?) (District )?\(B\)$', r'\1 City', n) # UTA
        n = re.sub(' District \(B\)$', ' Borough', n) # DIS
        n = re.sub(' \(B\)$', ' Borough', n) # DIS
        if self.area.type in ('CTY', 'DIS', 'LBO', 'UTA', 'MTD'): n += ' Council'
        n = re.sub(' (ED|CP)$', '', n) # CPC, CED, UTE
        n = re.sub(' Ward$', '', n) # DIW, LBW, MTW, UTW
        return n

    def save(self, *args, **kwargs):
        super(Name, self).save(*args, **kwargs)
        try:
            name = self.area.names.filter(type__in=('M', 'O', 'S')).order_by('type')[0]
            self.area.name = self.make_friendly_name(name)
            self.area.save()
        except:
            pass

class Code(models.Model):
    area = models.ForeignKey(Area, related_name='codes')
    type = models.CharField(max_length=10, choices=(
        ('ons', 'SNAC'),
        ('gss', 'GSS (SNAC replacement)'),
        ('unit_id', 'Boundary-Line (OS Admin Area ID)'),
        ('n5000', 'Norway code as given in N5000'),
    ))
    code = models.CharField(max_length=10)
    objects = Manager()

    class Meta:
        unique_together = ('area', 'type')

    def __unicode__(self):
        return '%s (%s) [%s]' % (self.code, self.type, self.area.id)
