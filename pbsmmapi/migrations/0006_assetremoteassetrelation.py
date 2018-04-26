# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-14 15:58
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pbsmmapi', '0005_auto_20180214_1552'),
    ]

    operations = [
        migrations.CreateModel(
            name='AssetRemoteAssetRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='remote_assets', to='pbsmmapi.PBSMMAsset')),
                ('remote_asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='pbsmmapi.PBSMMRemoteAsset')),
            ],
        ),
    ]