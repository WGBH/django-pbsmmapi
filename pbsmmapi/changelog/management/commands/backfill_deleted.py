from django.core.management.base import BaseCommand

from pbsmmapi.changelog.models import ChangeLog
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
            if ChangeLog.objects.filter(pk=log.pk, deleted__isnull=False).exists():
                marked += 1
        self.stdout.write(
            self.style.SUCCESS(f"Done. {marked} changelog(s) marked deleted.")
        )
