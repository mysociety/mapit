# Generated by Django 3.2.9 on 2021-11-04 10:21

import django.contrib.gis.db.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="UPRN",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("uprn", models.CharField(db_index=True, max_length=12, unique=True)),
                (
                    "postcode",
                    models.CharField(db_index=True, max_length=7, unique=True),
                ),
                ("location", django.contrib.gis.db.models.fields.PointField(srid=4326)),
            ],
            options={
                "ordering": ("uprn",),
            },
        ),
    ]
