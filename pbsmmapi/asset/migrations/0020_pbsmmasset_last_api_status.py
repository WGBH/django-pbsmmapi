# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-08 20:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0019_auto_20180207_1638'),
    ]

    operations = [
        migrations.AddField(
            model_name='pbsmmasset',
            name='last_api_status',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='Last API Status'),
        ),
    ]
