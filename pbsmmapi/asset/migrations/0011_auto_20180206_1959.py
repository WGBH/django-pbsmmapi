# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-06 19:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('asset', '0010_auto_20180206_1629'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='pbsmmasset',
            name='topics',
        ),
        migrations.AddField(
            model_name='pbsmmasset',
            name='language',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='Language'),
        ),
    ]
