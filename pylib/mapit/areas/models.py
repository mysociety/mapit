from django.contrib.gis.db import models

class GenerationManager(models.Manager):
    def current(self):
        return self.get_query_set().filter(active=True).order_by('-id')[0]

    def new(self):
        g = self.get_query_set().order_by('-id')[0]
        if g.active: return None
        return g
        
class Generation(models.Model):
    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    objects = GenerationManager()

    def __unicode__(self):
        return "Generation %d (%sactive)" % (self.id, "" if self.active else "in")

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

    objects = models.GeoManager()

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
        ('M', 'mySociety override'),
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
