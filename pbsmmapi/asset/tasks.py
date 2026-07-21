from huey import crontab
from huey.contrib.djhuey import (
    db_periodic_task,
    lock_task,
)

from pbsmmapi.asset.models import Asset


@db_periodic_task(crontab(minute="*/1"))
@lock_task("update-partial-assets")
def update_partial_assets() -> None:
    """
    Most Asset instances should have complete data, but in some cases we still
    have the partial "compact" version of the API data. We need to fetch the
    complete Asset data for many of the annotations to work.
    """
    incomplete_assets = Asset.objects.filter(
        data_format="compact",
        mm_content__last_api_status=200,
        mm_content__deleted__isnull=True,
    ).order_by("pk")
    for asset in incomplete_assets[:100]:
        asset.ingest_on_save = True
        asset.save()
