from huey import crontab
from huey.contrib.djhuey import (
    db_periodic_task,
    db_task,
)

from pbsmmapi.abstract.helpers import time_zone_aware_now
from pbsmmapi.api.api import get_PBSMM_record
from pbsmmapi.asset.models import Asset


@db_task(retries=3, retry_delay=10)
def get_complete_asset_data(asset: Asset) -> None:
    status, data = get_PBSMM_record(asset.api_endpoint)
    if status == 200:
        asset.json = data["data"]

    asset.last_api_status = status
    asset.date_last_api_update = time_zone_aware_now()
    asset.save()


@db_periodic_task(crontab(minute="*/1"))
def update_partial_assets() -> None:
    """
    When populating Assets, we use the Asset listing endpoint from the parent
    object. The data returned is incomplete, and notably does not contain
    caption or transcript data. The overall structure of the data differs
    between versions. The partial Asset dict contains a 'links' key, so that's
    the easiest way to detect whether we need to fetch and store the rest of
    the Asset data.

    The get_complete_asset_data method fetches and stores data from the Asset
    detail endpoint.

    We don't have a way to limit API calls globally, and this could execute
    simultaneously with any of the other API-calling tasks. As a safeguard, we
    limit to 100 requests/minute.
    """
    incomplete_assets = Asset.objects.filter(
        data_format="compact",
        last_api_status=200,
    )
    for asset in incomplete_assets[:100]:
        get_complete_asset_data(asset)
