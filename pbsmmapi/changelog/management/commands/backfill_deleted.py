from django.core.management.base import BaseCommand

from pbsmmapi.changelog.models import (
    ChangeLog,
    parse_changelog_timestamp,
)
from pbsmmapi.changelog.tasks import sync_deleted_state


class Command(BaseCommand):
    help = (
        "One-time backfill of deleted state from existing ChangeLog entries. "
        "Idempotent and safe to re-run; makes no API calls."
    )

    def handle(self, *args, **options):
        marked = 0
        for log in ChangeLog.objects.order_by("latest_timestamp").iterator():
            sync_deleted_state(log)
            if self._marks_deleted(log):
                marked += 1
        self.stdout.write(
            self.style.SUCCESS(f"Done. {marked} changelog(s) marked deleted.")
        )

    @staticmethod
    def _marks_deleted(log: ChangeLog) -> bool:
        # Mirror sync_deleted_state's decision from the in-memory entries so the
        # counter needs no per-row query: a log ends up deleted iff it has a
        # linked ContentRecord and its latest entry (by parsed timestamp, the
        # same ordering sync_deleted_state uses) is a "delete".
        if log.mm_content_id is None:
            return False
        latest = max(log.entries.keys(), default=None, key=parse_changelog_timestamp)
        return latest is not None and log.entries[latest].get("action") == "delete"
