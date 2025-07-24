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


def set_ingested():
    """
    If an object has already been ingested, we need to set the ingested boolean
    to True. This prevents unnecessary API calls.
    """
    querysets = [
        Franchise.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("object_id"),
                    ingested=False,
                )
            )
        ),
        Show.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("object_id"),
                    ingested=False,
                )
            )
        ),
        Special.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("object_id"),
                    ingested=False,
                )
            )
        ),
        Season.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("object_id"),
                    ingested=False,
                )
            )
        ),
        Episode.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("object_id"),
                    ingested=False,
                )
            )
        ),
        Asset.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("object_id"),
                    ingested=False,
                )
            )
        ),
    ]
    for queryset in filter(lambda qs: qs.exists(), querysets):
        ChangeLog.objects.filter(
            content_id__in=queryset.values_list("object_id")
        ).update(ingested=True)


def reingest_updated_objects():
    """
    When new actions appear in the changelog, we need to trigger
    ingest of the related object to get everything in sync.
    """
    querysets = [
        Franchise.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("object_id")))
        ),
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


def realize_provisional_objects():
    """
    For any provisional objects, we try to find matching Changelog entries and
    send the API data into the realize method.
    """
    realized_shows = []
    for show in Show.objects.filter(provisional=True):
        try:
            changelog = ShowChangeLog.objects.get(title=show.title)
            realized_show = Show.realize(changelog.api_data)
            realized_shows.append(realized_show)
        except ShowChangeLog.DoesNotExist:
            pass

    realized_seasons = []
    for season in Season.objects.filter(provisional=True):
        try:
            changelog = SeasonChangeLog.objects.get(
                show_id=season.show_api_id,
                ordinal=season.ordinal,
            )
            realized_season = Season.realize(changelog.api_data)
            realized_seasons.append(realized_season)
        except SeasonChangeLog.DoesNotExist:
            pass

    for episode in Episode.objects.filter(provisional=True):
        try:
            changelog = EpisodeChangeLog.objects.get(
                season_id=episode.season_api_id,
                ordinal=episode.ordinal,
            )
            Episode.realize(changelog.api_data)
        except EpisodeChangeLog.DoesNotExist:
            pass

    for special in Special.objects.filter(
        provisional=True,
    ):
        try:
            changelog = SpecialChangeLog.objects.get(
                show_id=special.show_api_id,
                title=special.title,
            )
            Special.realize(changelog.api_data)

        except SpecialChangeLog.DoesNotExist:
            pass

    for season in filter(None, realized_seasons):
        season.ingest_on_save = True
        season.ingest_episodes = True
        season.save()

    for show in filter(None, realized_shows):
        show.ingest_on_save = True
        show.ingest_seasons = True
        show.ingest_specials = True
        show.ingest_episodes = True
        show.save()


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
        realize_provisional_objects()


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
    set_ingested()

    remaining_api_calls = MAX_QUERIES - len(urls)
    get_changelog_data(remaining_api_calls)
