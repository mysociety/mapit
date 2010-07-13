from django.contrib.gis.db import models

class GenerationManager(models.Manager):
    def current(self):
        latest_on = self.get_query_set().filter(active=True).order_by('-id')
        if latest_on: return latest_on[0]
        return None

    def new(self):
        latest = self.get_query_set().order_by('-id')
        if not latest or latest[0].active:
            return None
        return latest[0]
        
class Generation(models.Model):
    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    objects = GenerationManager()

    def __unicode__(self):
        return "Generation %d (%sactive)" % (self.id, "" if self.active else "in")

class AreaManager(models.GeoManager):
    def get_or_create_with_name(self, country='', type='', name_type='', name=''):
        current_generation = Generation.objects.current()
        new_generation = Generation.objects.new()
        area, created = Area.objects.get_or_create(country=country, type=type,
            generation_low__lte=current_generation, generation_high__gte=current_generation,
            names__type=name_type, names__name=name,
            defaults = { 'generation_low': new_generation, 'generation_high': new_generation }
        )
        if created:
            area.names.get_or_create(type=type, name=name)
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
            area.codes.get_or_create(type=type, code=code)
        else:
            area.generation_high = new_generation
            area.save()
        return area

class Area(models.Model):
    parent_area = models.ForeignKey('self', related_name='children', null=True, blank=True)
    type = models.CharField(max_length=3, db_index=True, choices=(
        ('EUR', 'Euro region'),
        ('WMC', 'UK Parliament constituency'),
        ('Northern Ireland', (
            ('NIE', 'Northern Ireland Assembly constituency'),
            ('LGD', 'Council'),
            ('LGE', 'Council ward'),
        )),
        ('England', (
            ('CTY', 'County council'),
            ('CED', 'County council ward'),
            ('DIS', 'District council'),
            ('DIW', 'District council ward'),
            ('GLA', 'Greater London Authority'),
            ('LAC', 'London Assembly constituency'),
            ('LBO', 'London borough'),
            ('LBW', 'London borough ward'),
            ('MTD', 'Metropolitan district'),
            ('MTW', 'Metropolitan district ward'),
            ('COI', 'Scilly Isles'),
            ('COP', 'Scilly Isles "ward"'),
        )),
        ('SPC', 'Scottish Parliament constituency'),
        ('SPE', 'Scottish Parliament region'),
        ('WAC', 'Welsh Assembly constituency'),
        ('WAE', 'Welsh Assembly region'),
        ('UTA', 'Unitary Authority'),
        ('UTE', 'Unitary Authority ward (UTE)'),
        ('UTW', 'Unitary Authority ward (UTW)'),
        ('CPC', 'Civil Parish'),
    ))
    country = models.CharField(max_length=1, choices=(
        ('E', 'England'),
        ('W', 'Wales'),
        ('S', 'Scotland'),
        ('N', 'Northern Ireland'),
    ))
    generation_low = models.ForeignKey(Generation, related_name='new_areas')
    generation_high = models.ForeignKey(Generation, related_name='final_areas')
    polygon = models.MultiPolygonField(srid=27700, null=True, blank=True)

    objects = AreaManager()

    def name(self):
        for type in ('F', 'M', 'O', 'S'):
            try:
                return self.names.get(type=type)
            except:
                pass
        return '(Unknown)'

    def __unicode__(self):
        return '%s' % self.name()

    #def save(self, *args, **kwargs):
    #    super(Area, self).save(*args, **kwargs)

class Name(models.Model):
    area = models.ForeignKey(Area, related_name='names')
    type = models.CharField(max_length=1, choices=(
        ('O', 'Ordnance Survey'),
        ('S', 'ONS (SNAC/GSS)'),
        ('F', 'Display name'),
        ('M', 'mySociety name'),
    ))
    name = models.CharField(max_length=100)

    class Meta:
        unique_together = ('area', 'type')

    def __unicode__(self):
        return '%s (%s) [%s]' % (self.name, self.type, self.area.id)

class Code(models.Model):
    area = models.ForeignKey(Area, related_name='codes')
    type = models.CharField(max_length=10, choices=(
        ('ons', 'SNAC'),
        ('gss', 'GSS (SNAC replacement)'),
        ('unit_id', 'Boundary-Line (OS Admin Area ID)')
    ))
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        unique_together = ('area', 'type')

    def __unicode__(self):
        return '%s (%s) [%s]' % (self.code, self.type, self.area.id)
