# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-05 13:30
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PBSMMAsset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Not set by API', verbose_name='Created On')),
                ('date_last_api_update', models.DateTimeField(help_text='Not set by API', null=True, verbose_name='Last API Update')),
                ('ingest_on_save', models.BooleanField(default=False, help_text='If true, then will update values from the PBSMM API on save()', verbose_name='Ingest on Save')),
                ('title', models.CharField(blank=True, max_length=200, null=True, verbose_name='Title')),
                ('title_sortable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sortable Title')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Slug')),
                ('description_long', models.TextField(verbose_name='Long Description')),
                ('description_short', models.TextField(verbose_name='Short Description')),
                ('object_id', models.UUIDField(editable=False, unique=True, verbose_name='Object ID')),
                ('updated_on', models.DateTimeField(blank=True, null=True, verbose_name='Updated On')),
                ('legacy_tp_media_id', models.BigIntegerField(blank=True, help_text='COVE ID', null=True, unique=True, verbose_name='Legacy TP Media ID')),
                ('duration', models.IntegerField(blank=True, help_text='(in seconds)', null=True, verbose_name='Duration')),
                ('content_rating', models.CharField(blank=True, max_length=40, null=True, verbose_name='Content Rating')),
                ('has_captions', models.BooleanField(default=False, verbose_name='Has Captions')),
                ('is_excluded_from_dfp', models.BooleanField(default=False, verbose_name='Is excluded from DFP')),
                ('can_embed_player', models.BooleanField(default=False, verbose_name='Can Embed Player')),
                ('player_code', models.TextField(blank=True, null=True, verbose_name='Player Code')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PBSMMAssetAvailability',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group', models.CharField(choices=[('Station Members', 'station_members'), ('All Members', 'all_members'), ('Public', 'public')], max_length=40, verbose_name='Group')),
                ('updated_at', models.DateTimeField(blank=True, null=True, verbose_name='Updated At')),
                ('start', models.DateTimeField(blank=True, null=True, verbose_name='Start')),
                ('end', models.DateTimeField(blank=True, null=True, verbose_name='End')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.PBSMMAsset')),
            ],
        ),
        migrations.CreateModel(
            name='PBSMMAssetImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('profile', models.CharField(max_length=20, verbose_name='Profile')),
                ('image', models.CharField(max_length=100, verbose_name='Image URL')),
                ('updated_at', models.DateTimeField(verbose_name='Updated At')),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='asset.PBSMMAsset')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
