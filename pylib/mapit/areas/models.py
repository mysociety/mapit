from django.contrib.gis.db import models

class Generation(models.Model):
    active = models.BooleanField(default=False)
    created = models.DateTimeField()

class Area(models.Model):
    parent_area = models.ForeignKey('self', related_name='children', null=True)
    type = models.CharField(max_length=3)
    country = models.CharField(max_length=1, choices=(
        ('E', 'England'),
        ('W', 'Wales'),
        ('S', 'Scotland'),
        ('N', 'Northern Ireland'),
    ))
    generation_low = models.ForeignKey(Generation)
    generation_high = models.ForeignKey(Generation)
    polygon = models.MultiPolygonField(srid=27700, null=True)

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
