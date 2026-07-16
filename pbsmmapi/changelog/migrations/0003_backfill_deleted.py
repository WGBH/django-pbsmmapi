from datetime import (
    UTC,
    datetime,
)

from django.db import migrations

ASSET_PARENT_TYPES = {"franchise", "show", "season", "episode", "special"}


def parse_changelog_timestamp(timestamp: str) -> datetime:
    # frozen copy of changelog.models.parse_changelog_timestamp: data
    # migrations must not call live app code, which can change or move
    parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def backfill_deleted(apps, schema_editor):
    """
    One-time backfill of deleted state from pre-existing ChangeLog entries.
    Mirrors changelog.tasks.sync_deleted_state as of this migration: a row
    whose latest entry (by parsed instant) is a "delete" marks its
    ContentRecord and its direct assets' records. Deletes are terminal
    (recreation gets a new content ID; unpublish arrives as an update), so
    there is no clearing. Also recomputes latest_timestamp for rows saved
    when it was ordered lexicographically. Idempotent; makes no API calls.
    """
    ChangeLog = apps.get_model("changelog", "ChangeLog")
    ContentRecord = apps.get_model("record", "ContentRecord")
    Asset = apps.get_model("asset", "Asset")

    def direct_asset_record_ids(resource_type, content_id):
        # assets directly attached to the object; every other type gets its
        # own changelog delete entry (children are deleted before parents)
        if resource_type not in ASSET_PARENT_TYPES:
            return Asset.objects.none().values_list("mm_content_id", flat=True)
        return (
            Asset.objects.filter(**{f"{resource_type}__mm_content_id": content_id})
            .filter(mm_content__isnull=False)
            .values_list("mm_content_id", flat=True)
        )

    for log in ChangeLog.objects.order_by("latest_timestamp").iterator():
        latest = max(log.entries.keys(), default=None, key=parse_changelog_timestamp)
        latest_timestamp = (
            parse_changelog_timestamp(latest) if latest is not None else None
        )
        if latest_timestamp != log.latest_timestamp:
            # .update() avoids ChangeLog.save()'s side effects and its
            # NULL-mm_content assertion
            ChangeLog.objects.filter(pk=log.pk).update(
                latest_timestamp=latest_timestamp
            )
        if log.mm_content_id is None or latest is None:
            # no linked ContentRecord: nothing to mark, and a NULL id in the
            # asset filter would match assets of record-less parents
            continue
        if log.entries[latest].get("action") == "delete":
            ContentRecord.objects.filter(pk=log.mm_content_id).update(
                deleted=latest_timestamp
            )
            ContentRecord.objects.filter(
                pk__in=direct_asset_record_ids(log.resource_type, log.mm_content_id),
            ).update(deleted=latest_timestamp)


class Migration(migrations.Migration):

    dependencies = [
        ("changelog", "0002_remove_changelog_api_data_and_more"),
        ("record", "0002_contentrecord_added_deleted_field"),
        ("asset", "0011_remove_asset_api_endpoint_remove_asset_asset_type_and_more"),
    ]

    operations = [
        migrations.RunPython(
            backfill_deleted,
            migrations.RunPython.noop,
            elidable=True,
        ),
    ]
