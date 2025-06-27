from collections import defaultdict
from collections.abc import Iterable
from datetime import (
    UTC,
    datetime,
    timedelta,
)
from itertools import chain
from urllib.parse import (
    parse_qs,
    urlparse,
)

from django.db.models import (
    Exists,
    F,
    OuterRef,
)
from django.db.models.lookups import LessThan
from huey import crontab
from huey.contrib.djhuey import (
    db_periodic_task,
    db_task,
    lock_task,
    task,
)

from pbsmmapi.api.api import get_PBSMM_record
from pbsmmapi.asset.models import Asset
from pbsmmapi.changelog.models import (
    AssetChangeLog,
    ChangeLog,
    EpisodeChangeLog,
    SeasonChangeLog,
    ShowChangeLog,
    SpecialChangeLog,
)
from pbsmmapi.episode.models import Episode
from pbsmmapi.franchise.models import Franchise
from pbsmmapi.season.models import Season
from pbsmmapi.show.models import Show
from pbsmmapi.special.models import Special

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
    Group Changelog entries by UUID; combine attributes into a dict with
    timestamps as keys.
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
    """
    Using unified dict returned from prep_changelog_data, save ChangeLog
    instances for each content ID extracted from the changelog endpoint.
    """
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
    """
    Ensure we only fetch 400 changelog pages per minute.
    """
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


@db_task(retries=3)
def fetch_api_data(log: ChangeLog):
    status, data = get_PBSMM_record(log.api_url)
    log.api_status = status
    log.api_crawled = datetime.now(UTC)
    if status == 200:
        log.api_data = data
    log.save()


def ingest_new_objects():
    for franchise in Franchise.objects.all():
        show_logs = ShowChangeLog.objects.filter(
            franchise_id=franchise.object_id,
            ingested=False,
        )
        for log in show_logs:
            if log.get_instance() is not None:
                log.save()
            else:
                result = Show.realize(log.api_data)
                if result is False:
                    Show(object_id=log.content_id).save()
    for show in Show.objects.all():
        season_logs = SeasonChangeLog.objects.filter(
            show_id=show.object_id,
            ingested=False,
        )
        for log in season_logs:
            if log.get_instance() is not None:
                log.save()
            else:
                result = Season.realize(log.api_data)
                if result is False:
                    Season(object_id=log.content_id).save()

        episode_logs = EpisodeChangeLog.objects.filter(
            show_id=show.object_id,
            ingested=False,
        )
        for log in episode_logs:
            if log.get_instance() is not None:
                log.save()
            else:
                result = Episode.realize(log.api_data)
                if result is False:
                    Episode(object_id=log.content_id).save()

        special_logs = SpecialChangeLog.objects.filter(
            show_id=show.object_id,
            ingested=False,
        )
        for log in special_logs:
            if log.get_instance() is not None:
                log.save()
            else:
                result = Special.realize(log.api_data)
                if result is False:
                    Special(object_id=log.content_id).save()

    for log in AssetChangeLog.objects.exclude(parent_type__isnull=True):
        parent = log.get_parent_instance()
        if parent is not None:
            if not parent.assets.filter(object_id=log.content_id).exists():
                parent.ingest_on_save = True
                parent.save()


def reingest_updated_objects():
    for franchise in Franchise.objects.filter(
        Exists(ChangeLog.objects.filter(content_id=OuterRef("object_id")))
    ):
        changelog = ChangeLog.objects.get(content_id=franchise.object_id)
        if changelog.latest_timestamp > franchise.date_last_api_update:
            franchise.ingest_on_save = True
            franchise.save()

    querysets = [
        Show.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("object_id")))
        ),
        Special.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("object_id")))
        ),
        Season.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("object_id")))
        ),
        Episode.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("object_id")))
        ),
        Asset.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("object_id")))
        ),
    ]
    for queryset in querysets:
        for item in queryset:
            changelog = ChangeLog.objects.get(content_id=item.object_id)
            if changelog.latest_timestamp > item.date_last_api_update:
                item.ingest_on_save = True
                item.save()


def get_changelog_data(limit: int):
    """
    For ChangeLog objects we can't match with an ingested object, we
    need to fetch the API data in order to determine whether to ingest
    the object.
    """
    # for changelogs without API data
    logs = ChangeLog.objects.filter(
        api_status__isnull=True,
        ingested=False,
    )

    if logs.count() > limit:
        logs = logs[:limit]
        limit = 0
    else:
        limit = limit - logs.count()

    fetch_api_data.map(logs)

    # retry API fetch for objects that previously returned 403 or 404,
    # and which have been updated since the last API fetch attempt
    if limit > 0:
        logs = ChangeLog.objects.filter(
            api_status__in=[403, 404],
        ).filter(
            LessThan(
                F("api_crawled"),
                F("latest_timestamp"),
            )
        )

        if logs.count() > limit:
            logs = logs[:limit]
            limit = 0
        else:
            limit = limit - logs.count()

        fetch_api_data.map(logs)

    # at this point it's unlikely that we'll need to worry about going over the
    # API limit so we should just ingest new objects and update existing ones
    if limit > 0:
        reingest_updated_objects()
        ingest_new_objects()


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

    remaining_api_calls = MAX_QUERIES - len(urls)
    get_changelog_data(remaining_api_calls)
