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
            latest = max(
                log.entries.keys(), default=None, key=parse_changelog_timestamp
            )
            self._backfill_latest_timestamp(log, latest)
            sync_deleted_state(log)
            if self._marks_deleted(log, latest):
                marked += 1
        self.stdout.write(
            self.style.SUCCESS(f"Done. {marked} changelog(s) marked deleted.")
        )

    @staticmethod
    def _backfill_latest_timestamp(log: ChangeLog, latest: str | None) -> None:
        # Rows saved before ChangeLog.save() switched to parsed-instant ordering
        # kept a lexicographically-computed latest_timestamp. Recompute it here
        # (via .update(), avoiding save()'s get_instance/ingested side effects and
        # its NULL-mm_content assertion) so downstream ordering stays correct:
        # ChangeLog.objects.last() and the 403/404 retry's api_crawled < latest.
        latest_timestamp = (
            parse_changelog_timestamp(latest) if latest is not None else None
        )
        if latest_timestamp != log.latest_timestamp:
            ChangeLog.objects.filter(pk=log.pk).update(
                latest_timestamp=latest_timestamp
            )

    @staticmethod
    def _marks_deleted(log: ChangeLog, latest: str | None) -> bool:
        # Mirror sync_deleted_state's decision from the in-memory entries so the
        # counter needs no per-row query: a log ends up deleted iff it has a
        # linked ContentRecord and its latest entry (same parsed-instant order)
        # is a "delete".
        if log.mm_content_id is None or latest is None:
            return False
        return log.entries[latest].get("action") == "delete"
