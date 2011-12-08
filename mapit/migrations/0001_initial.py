# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):
    
    def forwards(self, orm):
        
        # Adding model 'Generation'
        db.create_table('mapit_generation', (
            ('active', self.gf('django.db.models.fields.BooleanField')(default=False, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('mapit', ['Generation'])

        # Adding model 'Country'
        db.create_table('mapit_country', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=1, unique=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, unique=True)),
        ))
        db.send_create_signal('mapit', ['Country'])

        # Adding model 'Type'
        db.create_table('mapit_type', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=3, unique=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
        ))
        db.send_create_signal('mapit', ['Type'])

        # Adding model 'Area'
        db.create_table('mapit_area', (
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('country', self.gf('django.db.models.fields.related.ForeignKey')(related_name='areas', blank=True, null=True, to=orm['mapit.Country'])),
            ('parent_area', self.gf('django.db.models.fields.related.ForeignKey')(related_name='children', blank=True, null=True, to=orm['mapit.Area'])),
            ('generation_high', self.gf('django.db.models.fields.related.ForeignKey')(related_name='final_areas', null=True, to=orm['mapit.Generation'])),
            ('generation_low', self.gf('django.db.models.fields.related.ForeignKey')(related_name='new_areas', null=True, to=orm['mapit.Generation'])),
            ('type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='areas', to=orm['mapit.Type'])),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('mapit', ['Area'])

        # Adding model 'Geometry'
        db.create_table('mapit_geometry', (
            ('polygon', self.gf('django.contrib.gis.db.models.fields.PolygonField')(srid=27700)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(related_name='polygons', to=orm['mapit.Area'])),
        ))
        db.send_create_signal('mapit', ['Geometry'])

        # Adding model 'Name'
        db.create_table('mapit_name', (
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(related_name='names', to=orm['mapit.Area'])),
        ))
        db.send_create_signal('mapit', ['Name'])

        # Adding unique constraint on 'Name', fields ['area', 'type']
        db.create_unique('mapit_name', ['area_id', 'type'])

        # Adding model 'Code'
        db.create_table('mapit_code', (
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('type', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('area', self.gf('django.db.models.fields.related.ForeignKey')(related_name='codes', to=orm['mapit.Area'])),
        ))
        db.send_create_signal('mapit', ['Code'])

        # Adding unique constraint on 'Code', fields ['area', 'type']
        db.create_unique('mapit_code', ['area_id', 'type'])

        # Adding model 'Postcode'
        db.create_table('mapit_postcode', (
            ('location', self.gf('django.contrib.gis.db.models.fields.PointField')(null=True)),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('postcode', self.gf('django.db.models.fields.CharField')(max_length=7, unique=True, db_index=True)),
        ))
        db.send_create_signal('mapit', ['Postcode'])

        # Adding M2M table for field areas on 'Postcode'
        db.create_table('mapit_postcode_areas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('postcode', models.ForeignKey(orm['mapit.postcode'], null=False)),
            ('area', models.ForeignKey(orm['mapit.area'], null=False))
        ))
        db.create_unique('mapit_postcode_areas', ['postcode_id', 'area_id'])
    
    
    def backwards(self, orm):
        
        # Deleting model 'Generation'
        db.delete_table('mapit_generation')

        # Deleting model 'Country'
        db.delete_table('mapit_country')

        # Deleting model 'Type'
        db.delete_table('mapit_type')

        # Deleting model 'Area'
        db.delete_table('mapit_area')

        # Deleting model 'Geometry'
        db.delete_table('mapit_geometry')

        # Deleting model 'Name'
        db.delete_table('mapit_name')

        # Removing unique constraint on 'Name', fields ['area', 'type']
        db.delete_unique('mapit_name', ['area_id', 'type'])

        # Deleting model 'Code'
        db.delete_table('mapit_code')

        # Removing unique constraint on 'Code', fields ['area', 'type']
        db.delete_unique('mapit_code', ['area_id', 'type'])

        # Deleting model 'Postcode'
        db.delete_table('mapit_postcode')

        # Removing M2M table for field areas on 'Postcode'
        db.delete_table('mapit_postcode_areas')
    
    
    models = {
        'mapit.area': {
            'Meta': {'object_name': 'Area'},
            'country': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'areas'", 'blank': 'True', 'null': 'True', 'to': "orm['mapit.Country']"}),
            'generation_high': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'final_areas'", 'null': 'True', 'to': "orm['mapit.Generation']"}),
            'generation_low': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'new_areas'", 'null': 'True', 'to': "orm['mapit.Generation']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'parent_area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'children'", 'blank': 'True', 'null': 'True', 'to': "orm['mapit.Area']"}),
            'type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'areas'", 'to': "orm['mapit.Type']"})
        },
        'mapit.code': {
            'Meta': {'unique_together': "(('area', 'type'),)", 'object_name': 'Code'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'codes'", 'to': "orm['mapit.Area']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'mapit.country': {
            'Meta': {'object_name': 'Country'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '1', 'unique': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'unique': 'True'})
        },
        'mapit.generation': {
            'Meta': {'object_name': 'Generation'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'mapit.geometry': {
            'Meta': {'object_name': 'Geometry'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'polygons'", 'to': "orm['mapit.Area']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polygon': ('django.contrib.gis.db.models.fields.PolygonField', [], {'srid': '27700'})
        },
        'mapit.name': {
            'Meta': {'unique_together': "(('area', 'type'),)", 'object_name': 'Name'},
            'area': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'names'", 'to': "orm['mapit.Area']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '10'})
        },
        'mapit.postcode': {
            'Meta': {'object_name': 'Postcode'},
            'areas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'postcodes'", 'blank': 'True', 'to': "orm['mapit.Area']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True'}),
            'postcode': ('django.db.models.fields.CharField', [], {'max_length': '7', 'unique': 'True', 'db_index': 'True'})
        },
        'mapit.type': {
            'Meta': {'object_name': 'Type'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '3', 'unique': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }
    
    complete_apps = ['mapit']
