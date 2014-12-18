# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mapit', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='generation',
            options={'ordering': ('id',)},
        ),
    ]
