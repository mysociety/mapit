# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.contrib.gis.db.models.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Area',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=2000, blank=True)),
            ],
            options={
                'ordering': ('name', 'type'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Code',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=500)),
                ('area', models.ForeignKey(related_name='codes', to='mapit.Area', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CodeType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(help_text=b"A unique code, eg 'ons' or 'unit_id'", unique=True, max_length=10)),
                ('description', models.CharField(help_text=b"The name of the code, eg 'Office of National Statitics' or 'Ordnance Survey ID'", max_length=200, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Country',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=3)),
                ('name', models.CharField(unique=True, max_length=100)),
            ],
            options={
                'verbose_name_plural': 'countries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Generation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(help_text=b"Describe this generation, eg '2010 electoral boundaries'", max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Geometry',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('polygon', django.contrib.gis.db.models.fields.PolygonField(srid=settings.MAPIT_AREA_SRID)),
                ('area', models.ForeignKey(related_name='polygons', to='mapit.Area', on_delete=models.CASCADE)),
            ],
            options={
                'verbose_name_plural': 'geometries',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Name',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=2000)),
                ('area', models.ForeignKey(related_name='names', to='mapit.Area', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='NameType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(help_text=b"A unique code to identify this type of name: eg 'english' or 'iso'", unique=True, max_length=10)),
                ('description', models.CharField(help_text=b"The name of this type of name, eg 'English' or 'ISO Standard'", max_length=200, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Postcode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('postcode', models.CharField(unique=True, max_length=7, db_index=True)),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True)),
                ('areas', models.ManyToManyField(related_name='postcodes', to='mapit.Area', blank=True)),
            ],
            options={
                'ordering': ('postcode',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Type',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(help_text=b"A unique code, eg 'CTR', 'CON', etc", unique=True, max_length=500)),
                ('description', models.CharField(help_text=b"The name of the type of area, eg 'Country', 'Constituency', etc", max_length=200, blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='name',
            name='type',
            field=models.ForeignKey(related_name='names', to='mapit.NameType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='name',
            unique_together=set([('area', 'type')]),
        ),
        migrations.AddField(
            model_name='code',
            name='type',
            field=models.ForeignKey(related_name='codes', to='mapit.CodeType', on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='code',
            unique_together=set([('area', 'type')]),
        ),
        migrations.AddField(
            model_name='area',
            name='country',
            field=models.ForeignKey(related_name='areas', blank=True, to='mapit.Country', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='area',
            name='generation_high',
            field=models.ForeignKey(related_name='final_areas', to='mapit.Generation', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='area',
            name='generation_low',
            field=models.ForeignKey(related_name='new_areas', to='mapit.Generation', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='area',
            name='parent_area',
            field=models.ForeignKey(related_name='children', blank=True, to='mapit.Area', null=True, on_delete=models.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='area',
            name='type',
            field=models.ForeignKey(related_name='areas', to='mapit.Type', on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]
