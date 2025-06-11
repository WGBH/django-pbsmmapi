from collections import defaultdict
from collections.abc import Iterable
from datetime import (
    datetime,
    timedelta,
)
from itertools import chain
from urllib.parse import (
    parse_qs,
    urlparse,
)

from huey import crontab
from huey.contrib.djhuey import (
    db_periodic_task,
    db_task,
    lock_task,
    task,
)

from pbsmmapi.api.api import get_PBSMM_record
from pbsmmapi.changelog.models import ChangeLog

BASE_CHANGELOG_URL = "https://media.services.pbs.org/api/v1/changelog/?sort=timestamp&type=asset&type=episode&type=franchise&type=season&type=show&type=special"

DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
MAX_QUERIES = 400


def default_changelog_dict():
    return {
        "resource_type": None,
        "changelogs": {},
    }


def prep_changelog_data(entries: Iterable[dict]) -> dict:
    """
    Group Changelog entries by UUID.
    """
    combined = defaultdict(default_changelog_dict)
    for changelog_dict in entries:
        content_id = changelog_dict.pop("id")
        resource_type = changelog_dict.pop("type")
        combined[content_id]["resource_type"] = resource_type
        attributes = changelog_dict.pop("attributes")
        timestamp = attributes.pop("timestamp")
        combined[content_id]["changelogs"][timestamp] = attributes
    return combined


@db_task(retries=3)
def save_changelog_entries(combined: dict):
    for content_id, data in combined.items():
        try:
            log = ChangeLog.objects.get(content_id=content_id)
        except ChangeLog.DoesNotExist:
            log = ChangeLog(
                content_id=content_id,
                resource_type=data["resource_type"],
            )
        for timestamp, entry in data["changelogs"].items():
            log.entries[timestamp] = entry
        log.save()


@task(retries=3, retry_delay=10)
def get_changelog_entries(url: str) -> list[dict]:
    status, mm_response_data = get_PBSMM_record(url)
    assert status == 200
    return mm_response_data["data"]


def max_page_number(mm_response_data: dict) -> int:
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
@lock_task("changelog-ingest")
def scrape_changelog():
    if not ChangeLog.objects.exists():
        # first time scraping, get first 400 pages
        urls = [f"{BASE_CHANGELOG_URL}&page={i}" for i in range(1, MAX_QUERIES)]
    else:
        most_recent_entry = ChangeLog.objects.last()
        assert most_recent_entry is not None
        assert most_recent_entry.latest_timestamp is not None
        # rewind 5 minutes to account for changelog entries added since
        # last crawl
        since = datetime.strftime(
            most_recent_entry.latest_timestamp - timedelta(minutes=5),
            DT_FORMAT,
        )
        base_url = f"{BASE_CHANGELOG_URL}&since={since}"

        _, mm_response_data = get_PBSMM_record(base_url)
        upper_page_bound = max_page_number(mm_response_data)
        urls = [f"{base_url}&page={i}" for i in range(1, upper_page_bound)]

    entries = get_changelog_entries.map(urls)
    data = prep_changelog_data(chain.from_iterable(entries.get(blocking=True)))
    save_changelog_entries(data)
