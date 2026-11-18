from django.db import migrations
from django.db.models import (
    F,
    OuterRef,
    Subquery,
)
from django.db.models.fields.json import KT

# Titles were only written on first ingest; copying the stored payload's
# title onto every row whose column has drifted from it.
MODELS = (
    ("franchise", "Franchise"),
    ("show", "Show"),
    ("season", "Season"),
    ("special", "Special"),
    ("episode", "Episode"),
    ("asset", "Asset"),
)


def backfill_titles(apps, schema_editor):
    ContentRecord = apps.get_model("record", "ContentRecord")
    payload_title = Subquery(
        ContentRecord.objects.filter(pk=OuterRef("mm_content_id"))
        .annotate(api_title=KT("api_data__data__attributes__title"))
        .values("api_title")[:1]
    )
    for app_label, model_name in MODELS:
        apps.get_model(app_label, model_name).objects.annotate(
            payload_title=payload_title
        ).filter(payload_title__isnull=False).exclude(title=F("payload_title")).update(
            title=F("payload_title")
        )


class Migration(migrations.Migration):
    dependencies = [
        ("record", "0002_contentrecord_added_deleted_field"),
        ("franchise", "0004_alter_franchise_options"),
        ("show", "0015_alter_show_options"),
        ("season", "0020_alter_season_options"),
        ("special", "0016_alter_special_options"),
        ("episode", "0020_alter_episode_options"),
        ("asset", "0011_remove_asset_api_endpoint_remove_asset_asset_type_and_more"),
    ]

    operations = [
        migrations.RunPython(backfill_titles, migrations.RunPython.noop),
    ]
