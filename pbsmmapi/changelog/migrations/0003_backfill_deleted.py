from django.db import migrations


def backfill_deleted(apps, schema_editor):
    """
    One-time backfill of deleted state from pre-existing ChangeLog entries:
    recompute latest_timestamp for rows saved when it was ordered
    lexicographically, then let sync_deleted_state mark the rows whose latest
    entry is a "delete" (deletes are terminal, there is no clearing).
    Idempotent; makes no API calls.

    Deliberately reuses the live changelog code instead of frozen copies so
    the backfill always applies the current delete semantics.
    """
    from pbsmmapi.abstract.helpers import parse_changelog_timestamp
    from pbsmmapi.changelog.models import ChangeLog
    from pbsmmapi.changelog.tasks import sync_deleted_state

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
        sync_deleted_state(log)


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
