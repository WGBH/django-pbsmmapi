# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-06 21:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0014_auto_20180206_2056'),
    ]

    operations = [
        migrations.AddField(
            model_name='pbsmmasset',
            name='platforms',
            field=models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Platforms'),
        ),
    ]
