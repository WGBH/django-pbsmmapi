# Generated by Django 5.1.2 on 2024-11-19 09:58

import pbsmmapi.abstract.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Franchise",
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
                (
                    "date_created",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Not set by API",
                        verbose_name="Created On",
                    ),
                ),
                (
                    "date_last_api_update",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Not set by API",
                        null=True,
                        verbose_name="Last API Retrieval",
                    ),
                ),
                (
                    "ingest_on_save",
                    models.BooleanField(
                        default=False,
                        help_text="If true, then will update values from the PBSMM API on save()",
                        verbose_name="Ingest on Save",
                    ),
                ),
                (
                    "last_api_status",
                    models.PositiveIntegerField(
                        blank=True, null=True, verbose_name="Last API Status"
                    ),
                ),
                (
                    "json",
                    models.JSONField(
                        blank=True,
                        help_text="This is the last JSON uploaded.",
                        null=True,
                        verbose_name="JSON",
                    ),
                ),
                (
                    "object_id",
                    models.UUIDField(
                        blank=True, null=True, unique=True, verbose_name="Object ID"
                    ),
                ),
                (
                    "api_endpoint",
                    models.URLField(
                        blank=True,
                        help_text="Endpoint to original record from the API",
                        null=True,
                        verbose_name="Link to API Record",
                    ),
                ),
                (
                    "title",
                    models.CharField(
                        blank=True, max_length=200, null=True, verbose_name="Title"
                    ),
                ),
                (
                    "title_sortable",
                    models.CharField(
                        blank=True,
                        max_length=200,
                        null=True,
                        verbose_name="Sortable Title",
                    ),
                ),
                (
                    "slug",
                    models.SlugField(max_length=200, unique=True, verbose_name="Slug"),
                ),
                ("description_long", models.TextField(verbose_name="Long Description")),
                (
                    "description_short",
                    models.TextField(verbose_name="Short Description"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        blank=True,
                        help_text="API record modified date",
                        null=True,
                        verbose_name="Updated At",
                    ),
                ),
                (
                    "premiered_on",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="Premiered On"
                    ),
                ),
                (
                    "nola",
                    models.CharField(
                        blank=True, max_length=8, null=True, verbose_name="NOLA Code"
                    ),
                ),
                (
                    "images",
                    models.JSONField(
                        blank=True,
                        help_text="JSON serialized field",
                        null=True,
                        verbose_name="Images",
                    ),
                ),
                (
                    "funder_message",
                    models.TextField(
                        blank=True, null=True, verbose_name="Funder Message"
                    ),
                ),
                (
                    "is_excluded_from_dfp",
                    models.BooleanField(
                        default=False, verbose_name="Is excluded from DFP"
                    ),
                ),
                (
                    "can_embed_player",
                    models.BooleanField(default=False, verbose_name="Can Embed Player"),
                ),
                (
                    "links",
                    models.JSONField(
                        blank=True,
                        help_text="JSON serialized field",
                        null=True,
                        verbose_name="Links",
                    ),
                ),
                (
                    "platforms",
                    models.JSONField(
                        blank=True,
                        help_text="JSON serialized field",
                        null=True,
                        verbose_name="Platforms",
                    ),
                ),
                (
                    "ga_page",
                    models.CharField(
                        blank=True, max_length=40, null=True, verbose_name="GA Page Tag"
                    ),
                ),
                (
                    "ga_event",
                    models.CharField(
                        blank=True,
                        max_length=40,
                        null=True,
                        verbose_name="GA Event Tag",
                    ),
                ),
                (
                    "genre",
                    models.JSONField(
                        blank=True,
                        help_text="JSON Serialized Field",
                        null=True,
                        verbose_name="Genre",
                    ),
                ),
                (
                    "hashtag",
                    models.CharField(
                        blank=True, max_length=100, null=True, verbose_name="Hashtag"
                    ),
                ),
                (
                    "ingest_shows",
                    models.BooleanField(
                        default=False,
                        help_text="Also ingest all Shows",
                        verbose_name="Ingest Shows",
                    ),
                ),
                (
                    "ingest_seasons",
                    models.BooleanField(
                        default=False,
                        help_text="Also ingest all Seasons (for each Show)",
                        verbose_name="Ingest Seasons",
                    ),
                ),
                (
                    "ingest_specials",
                    models.BooleanField(
                        default=False,
                        help_text="Also ingest all Show Specials",
                        verbose_name="Ingest Specials",
                    ),
                ),
                (
                    "ingest_episodes",
                    models.BooleanField(
                        default=False,
                        help_text="Also ingest all Episodes (for each Season)",
                        verbose_name="Ingest Episodes",
                    ),
                ),
            ],
            options={
                "verbose_name": "PBS MM Franchise",
                "verbose_name_plural": "PBS MM Franchises",
                "db_table": "pbsmm_franchise",
            },
            bases=(pbsmmapi.abstract.models.AssetAvailablitiesMixin, models.Model),
        ),
    ]
