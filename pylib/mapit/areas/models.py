from django.contrib.gis.db import models

class Generation(models.Model):
    active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

class Area(models.Model):
    parent_area = models.ForeignKey('self', related_name='children', null=True, blank=True)
    type = models.CharField(max_length=3, db_index=True, choices=(
        ('COI', 'Scilly Isles'),
        ('COP', 'Scilly Isles "ward"'),
        ('CPC', 'Civil Parish'),
        ('CTY', 'County council'),
        ('CED', 'County council ward'),
        ('DIS', 'District council'),
        ('DIW', 'District council ward'),
        ('EUR', 'Euro region'),
        ('GLA', 'Greater London Authority'),
        ('LAC', 'London Assembly Constituency'),
        ('LBO', 'London Borough'),
        ('LBW', 'London Borough Ward'),
        ('LGD', 'NI Council'),
        ('LGE', 'NI Council Ward'),
        ('MTD', 'Metropolitan District'),
        ('MTW', 'Metropolitan District Ward'),
        ('NIE', 'Northern Ireland Assembly Constituency'),
        ('SPC', 'Scottish Parliament Constituency'),
        ('SPE', 'Scottish Parliament Region'),
        ('UTA', 'Unitary Authority'),
        ('UTE', 'Unitary Authority Ward (UTE)'),
        ('UTW', 'Unitary Authority Ward (UTW)'),
        ('WAC', 'Welsh Assembly Constituency'),
        ('WAE', 'Welsh Assembly Region'),
        ('WMC', 'UK Parliament'),
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
        return self.names.get(type='F')

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
        ('ons_code', 'SNAC'),
        ('gss', 'GSS (SNAC replacement)'),
        ('unit_id', 'Boundary-Line (OS Admin Area ID)')
    ))
    code = models.CharField(max_length=10, unique=True)

    class Meta:
        unique_together = ('area', 'type')

    def __unicode__(self):
        return '%s (%s) [%s]' % (self.code, self.type, self.area.id)
