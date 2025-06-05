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
from pbsmmapi.changelog.models import ChangeLogEntry

BASE_CHANGELOG_URL = "https://media.services.pbs.org/api/v1/changelog/?sort=timestamp&type=asset&type=episode&type=franchise&type=season&type=show&type=special"

DT_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
MAX_QUERIES = 400


@db_task(retries=3)
def process_changelog_entries(overall_changelog_dict: dict):
    for changelog_id, changelog_dict in overall_changelog_dict.items():
        try:
            ChangeLogEntry.objects.get(
                content_id=changelog_id,
                timestamp=changelog_dict["timestamp"],
            )
        except ChangeLogEntry.DoesNotExist:
            changelog_entry = ChangeLogEntry.objects.create(
                resource_type=changelog_dict["type"],
                content_id=changelog_id,
                timestamp=changelog_dict["timestamp"],
                api_data=changelog_dict["api_data"],
            )
            changelog_entry.process()


@db_task(retries=3)
def add_changelog_entries(url: str, overall_changelog_dict: dict):
    """
    Add either a new changelog ID event or update an existing one from the current scraping.
    Since we need to hit the same MM API regardless of whether it's a create or update event,
    we only need to have the correct MM object id with its latest changelog data.
    """
    _, mm_response_data = get_PBSMM_record(url)
    changelog_dicts = mm_response_data["data"]
    for changelog_dict in changelog_dicts:
        timestamp = changelog_dict["attributes"]["timestamp"]
        date_time = datetime.fromisoformat(timestamp)
        overall_changelog_dict[changelog_dict["id"]] = {
            "type": changelog_dict["type"],
            "timestamp": date_time,
            "api_data": changelog_dict,
        }


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
    overall_changelog_dict = {}
    if ChangeLogEntry.objects.exists() is False:
        # first time scraping, get first 400 pages
        for i in range(1, MAX_QUERIES):
            url = f"{BASE_CHANGELOG_URL}&page={i}"
            add_changelog_entries(url, overall_changelog_dict)
    else:
        most_recent_entry = ChangeLogEntry.objects.last()
        # rewind 5 minutes to account for changelog entries added since
        # last crawl
        since = datetime.strftime(
            most_recent_entry.timestamp - timedelta(minutes=5),
            DT_FORMAT,
        )
        base_url = f"{BASE_CHANGELOG_URL}&since={since}"
        _, mm_response_data = get_PBSMM_record(base_url)
        upper_page_bound = max_page_number(mm_response_data)
        for i in range(1, upper_page_bound):
            url = f"{base_url}&page={i}"
            add_changelog_entries(url, overall_changelog_dict)
    process_changelog_entries(overall_changelog_dict)
