# -*- coding: utf-8 -*-
# Generated by Django 1.11.9 on 2018-02-13 15:42
from __future__ import unicode_literals

from django.db import migrations, models


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
                ('date_last_api_update', models.DateTimeField(help_text='Not set by API', null=True, verbose_name='Last API Retrieval')),
                ('ingest_on_save', models.BooleanField(default=False, help_text='If true, then will update values from the PBSMM API on save()', verbose_name='Ingest on Save')),
                ('last_api_status', models.PositiveIntegerField(blank=True, null=True, verbose_name='Last API Status')),
                ('object_id', models.UUIDField(blank=True, null=True, unique=True, verbose_name='Object ID')),
                ('link_to_api_record', models.URLField(blank=True, help_text='Endpoint to original record from the API', null=True, verbose_name='Link to API Record')),
                ('title', models.CharField(blank=True, max_length=200, null=True, verbose_name='Title')),
                ('title_sortable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sortable Title')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Slug')),
                ('description_long', models.TextField(verbose_name='Long Description')),
                ('description_short', models.TextField(verbose_name='Short Description')),
                ('updated_at', models.DateTimeField(blank=True, help_text='API record modified date', null=True, verbose_name='Updated At')),
                ('images', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Images')),
                ('funder_message', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Funder Message')),
                ('is_excluded_from_dfp', models.BooleanField(default=False, verbose_name='Is excluded from DFP')),
                ('can_embed_player', models.BooleanField(default=False, verbose_name='Can Embed Player')),
                ('links', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Links')),
                ('platforms', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Platforms')),
                ('windows', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Windows')),
                ('geo_profile', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Geo Profile')),
                ('language', models.CharField(blank=True, max_length=10, null=True, verbose_name='Language')),
                ('legacy_tp_media_id', models.BigIntegerField(blank=True, help_text='(Legacy TP Media ID)', null=True, unique=True, verbose_name='COVE ID')),
                ('availability', models.TextField(blank=True, help_text='JSON serialized Field', null=True, verbose_name='Availability')),
                ('duration', models.IntegerField(blank=True, help_text='(in seconds)', null=True, verbose_name='Duration')),
                ('object_type', models.CharField(blank=True, max_length=40, null=True, verbose_name='Object Type')),
                ('has_captions', models.BooleanField(default=False, verbose_name='Has Captions')),
                ('tags', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Tags')),
                ('topics', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Topics')),
                ('player_code', models.TextField(blank=True, null=True, verbose_name='Player Code')),
                ('chapters', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Chapters')),
                ('content_rating', models.CharField(blank=True, max_length=100, null=True, verbose_name='Content Rating')),
                ('content_rating_description', models.TextField(blank=True, null=True, verbose_name='Content Rating Description')),
            ],
            options={
                'db_table': 'pbsmm_asset',
                'verbose_name': 'PBS Media Manager Asset',
                'verbose_name_plural': 'PBS Media Manager Assets',
            },
        ),
        migrations.CreateModel(
            name='PBSMMEpisode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Not set by API', verbose_name='Created On')),
                ('date_last_api_update', models.DateTimeField(help_text='Not set by API', null=True, verbose_name='Last API Retrieval')),
                ('ingest_on_save', models.BooleanField(default=False, help_text='If true, then will update values from the PBSMM API on save()', verbose_name='Ingest on Save')),
                ('last_api_status', models.PositiveIntegerField(blank=True, null=True, verbose_name='Last API Status')),
                ('object_id', models.UUIDField(blank=True, null=True, unique=True, verbose_name='Object ID')),
                ('link_to_api_record', models.URLField(blank=True, help_text='Endpoint to original record from the API', null=True, verbose_name='Link to API Record')),
                ('title', models.CharField(blank=True, max_length=200, null=True, verbose_name='Title')),
                ('title_sortable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sortable Title')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Slug')),
                ('description_long', models.TextField(verbose_name='Long Description')),
                ('description_short', models.TextField(verbose_name='Short Description')),
                ('updated_at', models.DateTimeField(blank=True, help_text='API record modified date', null=True, verbose_name='Updated At')),
                ('premiered_on', models.DateTimeField(blank=True, null=True, verbose_name='Premiered On')),
                ('nola', models.CharField(blank=True, max_length=8, null=True, verbose_name='NOLA Code')),
                ('funder_message', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Funder Message')),
                ('links', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Links')),
                ('language', models.CharField(blank=True, max_length=10, null=True, verbose_name='Language')),
                ('encored_on', models.DateTimeField(blank=True, null=True, verbose_name='Encored On')),
                ('ordinal', models.PositiveIntegerField(blank=True, null=True, verbose_name='Ordinal')),
                ('segment', models.PositiveIntegerField(blank=True, null=True, verbose_name='Segment')),
            ],
            options={
                'db_table': 'pbsmm_episode',
                'verbose_name': 'PBS Medio Manager Episode',
                'verbose_name_plural': 'PBS Media Manager Episodes',
            },
        ),
        migrations.CreateModel(
            name='PBSMMRemoteAsset',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Not set by API', verbose_name='Created On')),
                ('date_last_api_update', models.DateTimeField(help_text='Not set by API', null=True, verbose_name='Last API Retrieval')),
                ('ingest_on_save', models.BooleanField(default=False, help_text='If true, then will update values from the PBSMM API on save()', verbose_name='Ingest on Save')),
                ('last_api_status', models.PositiveIntegerField(blank=True, null=True, verbose_name='Last API Status')),
                ('object_id', models.UUIDField(blank=True, null=True, unique=True, verbose_name='Object ID')),
                ('link_to_api_record', models.URLField(blank=True, help_text='Endpoint to original record from the API', null=True, verbose_name='Link to API Record')),
                ('title', models.CharField(blank=True, max_length=200, null=True, verbose_name='Title')),
                ('title_sortable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sortable Title')),
                ('description_long', models.TextField(verbose_name='Long Description')),
                ('description_short', models.TextField(verbose_name='Short Description')),
                ('updated_at', models.DateTimeField(blank=True, help_text='API record modified date', null=True, verbose_name='Updated At')),
                ('tags', models.TextField(blank=True, null=True, verbose_name='Tags')),
                ('remote_url', models.URLField(blank=True, null=True, verbose_name='URL')),
            ],
            options={
                'db_table': 'pbsmm_remoteasset',
                'verbose_name': 'PBS Media Manager Remote Asset',
                'verbose_name_plural': 'PBS Media Manager Remote Assets',
            },
        ),
        migrations.CreateModel(
            name='PBSMMSeason',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Not set by API', verbose_name='Created On')),
                ('date_last_api_update', models.DateTimeField(help_text='Not set by API', null=True, verbose_name='Last API Retrieval')),
                ('ingest_on_save', models.BooleanField(default=False, help_text='If true, then will update values from the PBSMM API on save()', verbose_name='Ingest on Save')),
                ('last_api_status', models.PositiveIntegerField(blank=True, null=True, verbose_name='Last API Status')),
                ('object_id', models.UUIDField(blank=True, null=True, unique=True, verbose_name='Object ID')),
                ('link_to_api_record', models.URLField(blank=True, help_text='Endpoint to original record from the API', null=True, verbose_name='Link to API Record')),
                ('title', models.CharField(blank=True, max_length=200, null=True, verbose_name='Title')),
                ('title_sortable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sortable Title')),
                ('description_long', models.TextField(verbose_name='Long Description')),
                ('description_short', models.TextField(verbose_name='Short Description')),
                ('updated_at', models.DateTimeField(blank=True, help_text='API record modified date', null=True, verbose_name='Updated At')),
                ('images', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Images')),
                ('links', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Links')),
                ('ordinal', models.PositiveIntegerField(blank=True, null=True, verbose_name='Ordinal')),
            ],
            options={
                'db_table': 'pbsmm_season',
                'verbose_name': 'PBS Media Manager Season',
                'verbose_name_plural': 'PBS Media Manager Seasons',
            },
        ),
        migrations.CreateModel(
            name='PBSMMShow',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Not set by API', verbose_name='Created On')),
                ('date_last_api_update', models.DateTimeField(help_text='Not set by API', null=True, verbose_name='Last API Retrieval')),
                ('ingest_on_save', models.BooleanField(default=False, help_text='If true, then will update values from the PBSMM API on save()', verbose_name='Ingest on Save')),
                ('last_api_status', models.PositiveIntegerField(blank=True, null=True, verbose_name='Last API Status')),
                ('object_id', models.UUIDField(blank=True, null=True, unique=True, verbose_name='Object ID')),
                ('link_to_api_record', models.URLField(blank=True, help_text='Endpoint to original record from the API', null=True, verbose_name='Link to API Record')),
                ('title', models.CharField(blank=True, max_length=200, null=True, verbose_name='Title')),
                ('title_sortable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sortable Title')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Slug')),
                ('description_long', models.TextField(verbose_name='Long Description')),
                ('description_short', models.TextField(verbose_name='Short Description')),
                ('updated_at', models.DateTimeField(blank=True, help_text='API record modified date', null=True, verbose_name='Updated At')),
                ('premiered_on', models.DateTimeField(blank=True, null=True, verbose_name='Premiered On')),
                ('nola', models.CharField(blank=True, max_length=8, null=True, verbose_name='NOLA Code')),
                ('images', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Images')),
                ('funder_message', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Funder Message')),
                ('is_excluded_from_dfp', models.BooleanField(default=False, verbose_name='Is excluded from DFP')),
                ('can_embed_player', models.BooleanField(default=False, verbose_name='Can Embed Player')),
                ('links', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Links')),
                ('platforms', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Platforms')),
                ('ga_page', models.CharField(blank=True, max_length=40, null=True, verbose_name='GA Page Tag')),
                ('ga_event', models.CharField(blank=True, max_length=40, null=True, verbose_name='GA Event Tag')),
                ('genre', models.TextField(blank=True, help_text='JSON Serialized Field', null=True, verbose_name='Genre')),
                ('episode_count', models.PositiveIntegerField(blank=True, null=True, verbose_name='Episode Count')),
                ('display_episode_number', models.BooleanField(default=False, verbose_name='Display Episode Number')),
                ('sort_episodes_descending', models.BooleanField(default=False, verbose_name='Sort Episodes Descending')),
                ('ordinal_season', models.BooleanField(default=True, verbose_name='Ordinal Season')),
                ('language', models.CharField(blank=True, max_length=10, null=True, verbose_name='Language')),
                ('audience', models.TextField(blank=True, help_text='JSON Serialized Field', null=True, verbose_name='Audience')),
                ('hashtag', models.CharField(blank=True, max_length=100, null=True, verbose_name='Hashtag')),
            ],
            options={
                'db_table': 'pbsmm_show',
                'verbose_name': 'PBS Media Manager Show',
                'verbose_name_plural': 'PBS Media Manager Shows',
            },
        ),
        migrations.CreateModel(
            name='PBSMMSpecial',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, help_text='Not set by API', verbose_name='Created On')),
                ('date_last_api_update', models.DateTimeField(help_text='Not set by API', null=True, verbose_name='Last API Retrieval')),
                ('ingest_on_save', models.BooleanField(default=False, help_text='If true, then will update values from the PBSMM API on save()', verbose_name='Ingest on Save')),
                ('last_api_status', models.PositiveIntegerField(blank=True, null=True, verbose_name='Last API Status')),
                ('object_id', models.UUIDField(blank=True, null=True, unique=True, verbose_name='Object ID')),
                ('link_to_api_record', models.URLField(blank=True, help_text='Endpoint to original record from the API', null=True, verbose_name='Link to API Record')),
                ('title', models.CharField(blank=True, max_length=200, null=True, verbose_name='Title')),
                ('title_sortable', models.CharField(blank=True, max_length=200, null=True, verbose_name='Sortable Title')),
                ('slug', models.SlugField(max_length=200, unique=True, verbose_name='Slug')),
                ('description_long', models.TextField(verbose_name='Long Description')),
                ('description_short', models.TextField(verbose_name='Short Description')),
                ('updated_at', models.DateTimeField(blank=True, help_text='API record modified date', null=True, verbose_name='Updated At')),
                ('premiered_on', models.DateTimeField(blank=True, null=True, verbose_name='Premiered On')),
                ('nola', models.CharField(blank=True, max_length=8, null=True, verbose_name='NOLA Code')),
                ('links', models.TextField(blank=True, help_text='JSON serialized field', null=True, verbose_name='Links')),
                ('language', models.CharField(blank=True, max_length=10, null=True, verbose_name='Language')),
                ('encored_on', models.DateTimeField(blank=True, null=True, verbose_name='Encored On')),
            ],
            options={
                'db_table': 'pbsmm_special',
                'verbose_name': 'PBS Media Manager Special',
                'verbose_name_plural': 'PBS Media Manager Specials',
            },
        ),
    ]