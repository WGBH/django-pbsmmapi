from datetime import (
    datetime,
    timedelta,
)
from urllib.parse import (
    parse_qs,
    urlparse,
)

from huey import crontab
from huey.contrib.djhuey import (
    db_periodic_task,
    db_task,
)

from pbsmmapi.api.api import get_PBSMM_record
from pbsmmapi.changelog.models import ChangeLog

BASE_CHANGELOG_URL = "https://media.services.pbs.org/api/v1/changelog/?sort=timestamp&type=asset&type=episode&type=franchise&type=season&type=show&type=special"

DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
MAX_QUERIES = 400


@db_task(retries=3)
def save_changelog_entries(url: str):
    _, mm_response_data = get_PBSMM_record(url)
    changelog_dicts = mm_response_data["data"]
    for changelog_dict in changelog_dicts:
        try:
            log = ChangeLog.objects.get(
                content_id=changelog_dict["id"],
                resource_type=changelog_dict["type"],
            )
        except ChangeLog.DoesNotExist:
            log = ChangeLog(
                content_id=changelog_dict["id"],
                resource_type=changelog_dict["type"],
            )

        timestamp = changelog_dict["attributes"].pop("timestamp")
        if timestamp not in log.entries.keys():
            log.entries[timestamp] = changelog_dict["attributes"]
            log.save()


def max_page_number(mm_response_data: dict):
    links: dict = mm_response_data.get("links", dict())
    last: str = links.get("last", "")
    parsed = urlparse(last)
    query_params = parse_qs(parsed.query)
    try:
        last_page = int(query_params["page"][0])
    except KeyError:
        last_page = 0

    if last_page > MAX_QUERIES:
        return MAX_QUERIES + 1
    else:
        return last_page + 1


@db_periodic_task(crontab(minute="*/1"))
def scrape_changelog():
    if ChangeLog.objects.exists() is False:
        # first time scraping, get first 400 pages
        for i in range(1, MAX_QUERIES):
            url = f"{BASE_CHANGELOG_URL}&page={i}"
            save_changelog_entries(url)
    else:
        most_recent_entry = ChangeLog.objects.last()
        assert most_recent_entry is not None
        # rewind 5 minutes to account for changelog entries added since
        # last crawl
        since = datetime.strftime(
            most_recent_entry.latest_timestamp - timedelta(minutes=5),
            DT_FORMAT,
        )
        base_url = f"{BASE_CHANGELOG_URL}&since={since}"

        _, mm_response_data = get_PBSMM_record(base_url)
        upper_page_bound = max_page_number(mm_response_data)
        for i in range(1, upper_page_bound):
            url = f"{base_url}&page={i}"
            save_changelog_entries(url)
