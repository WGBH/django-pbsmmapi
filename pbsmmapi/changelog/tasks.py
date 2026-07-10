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
    Q,
    QuerySet,
    Subquery,
)
from django.db.models.lookups import LessThan
from huey import crontab
from huey.contrib.djhuey import (
    HUEY,
    db_periodic_task,
    db_task,
    lock_task,
    task,
)

from pbsmmapi.abstract.constants import PBSMM_BASE_URL
from pbsmmapi.api.api import get_PBSMM_record
from pbsmmapi.asset.models import Asset
from pbsmmapi.changelog.models import (
    AssetChangeLog,
    ChangeLog,
    EpisodeChangeLog,
    SeasonChangeLog,
    ShowChangeLog,
    SpecialChangeLog,
    parse_changelog_timestamp,
)
from pbsmmapi.episode.models import Episode
from pbsmmapi.franchise.models import Franchise
from pbsmmapi.record.models import ContentRecord
from pbsmmapi.season.models import Season
from pbsmmapi.show.models import Show
from pbsmmapi.special.models import Special

BASE_CHANGELOG_URL = f"{PBSMM_BASE_URL}api/v1/changelog/?sort=timestamp&type=asset&type=episode&type=franchise&type=season&type=show&type=special"

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


def descendant_querysets(resource_type: str, content_id) -> list[QuerySet]:
    """
    Querysets of every object that becomes unreachable in the API when the
    given object is deleted. Objects are keyed by their ContentRecord
    (``mm_content_id`` equals the changelog ``content_id``).
    """
    if resource_type == "franchise":
        return [
            Show.objects.filter(franchise__mm_content_id=content_id),
            Season.objects.filter(show__franchise__mm_content_id=content_id),
            Episode.objects.filter(season__show__franchise__mm_content_id=content_id),
            Special.objects.filter(show__franchise__mm_content_id=content_id),
            Asset.objects.filter(
                Q(franchise__mm_content_id=content_id)
                | Q(show__franchise__mm_content_id=content_id)
                | Q(season__show__franchise__mm_content_id=content_id)
                | Q(episode__season__show__franchise__mm_content_id=content_id)
                | Q(special__show__franchise__mm_content_id=content_id)
            ),
        ]
    if resource_type == "show":
        return [
            Season.objects.filter(show__mm_content_id=content_id),
            Episode.objects.filter(season__show__mm_content_id=content_id),
            Special.objects.filter(show__mm_content_id=content_id),
            Asset.objects.filter(
                Q(show__mm_content_id=content_id)
                | Q(season__show__mm_content_id=content_id)
                | Q(episode__season__show__mm_content_id=content_id)
                | Q(special__show__mm_content_id=content_id)
            ),
        ]
    if resource_type == "season":
        return [
            Episode.objects.filter(season__mm_content_id=content_id),
            Asset.objects.filter(
                Q(season__mm_content_id=content_id)
                | Q(episode__season__mm_content_id=content_id)
            ),
        ]
    if resource_type == "episode":
        return [Asset.objects.filter(episode__mm_content_id=content_id)]
    if resource_type == "special":
        return [Asset.objects.filter(special__mm_content_id=content_id)]
    return []


def descendant_record_ids(queryset: QuerySet) -> QuerySet:
    return queryset.filter(mm_content__isnull=False).values_list(
        "mm_content_id",
        flat=True,
    )


def mark_deleted(log: ChangeLog, deleted_at: datetime):
    """
    Record a delete on all layers: the object's ContentRecord, its
    descendants' records, and the ChangeLog itself all get the entry's
    timestamp, overwriting any earlier value — ``deleted`` always holds the
    most recent delete reported for the subtree. Nothing correlates the
    timestamps afterwards (clear_deleted resyncs from each object's own
    changelog mirror), so the overwrite is idempotent and safe for stale
    instances and concurrent runs.

    Everything uses queryset .update(): no save()/ingest side effects.
    A descendant whose ``mm_content`` is NULL has no record to mark and is
    skipped.
    """
    ContentRecord.objects.filter(pk=log.mm_content_id).update(deleted=deleted_at)
    for queryset in descendant_querysets(log.resource_type, log.mm_content_id):
        ContentRecord.objects.filter(
            pk__in=descendant_record_ids(queryset),
        ).update(deleted=deleted_at)
    ChangeLog.objects.filter(pk=log.pk).update(deleted=deleted_at)


def clear_deleted(log: ChangeLog):
    """
    Un-delete after a changelog entry newer than the delete: clear the
    object's own record and mirror, and resync every descendant's record to
    its OWN changelog mirror — the per-object source of truth. A descendant
    deleted by its own changelog entry gets its own timestamp back and stays
    deleted; everything the cascade marked goes back to NULL.

    Known edge: a descendant of a still-deleted intermediate parent resyncs
    to alive (its own mirror is NULL); the intermediate's next changelog
    entry or a backfill re-marks it.
    """
    ContentRecord.objects.filter(pk=log.mm_content_id).update(deleted=None)
    own_mirror = ChangeLog.objects.filter(mm_content_id=OuterRef("pk")).values(
        "deleted"
    )[:1]
    for queryset in descendant_querysets(log.resource_type, log.mm_content_id):
        ContentRecord.objects.filter(
            pk__in=descendant_record_ids(queryset),
        ).update(deleted=Subquery(own_mirror))
    ChangeLog.objects.filter(pk=log.pk).update(deleted=None)


def sync_deleted_state(log: ChangeLog):
    """
    Record the delete when the latest changelog entry action is "delete";
    clear the mark when a newer entry supersedes the delete. Idempotent.

    "Latest" is decided by parsed timestamp, not string order, so entries
    whose formats differ (e.g. missing microseconds or offsets) still compare
    chronologically.
    """
    timestamp = max(log.entries.keys(), default=None, key=parse_changelog_timestamp)
    if timestamp is None:
        return
    if log.entries[timestamp].get("action") == "delete":
        mark_deleted(log, parse_changelog_timestamp(timestamp))
    elif ChangeLog.objects.filter(pk=log.pk, deleted__isnull=False).exists():
        clear_deleted(log)


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
            record, _ = ContentRecord.objects.get_or_create(
                content_id=content_id,
            )
            log = ChangeLog(
                resource_type=data["resource_type"],
                mm_content=record,
            )
        for timestamp, entry in data["changelogs"].items():
            log.entries[timestamp] = entry
        log.save()
        sync_deleted_state(log)


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
    return last_page


@db_task(retries=3)
def fetch_api_data(log: ChangeLog):
    status, data = get_PBSMM_record(log.api_url)
    content_record = log.mm_content
    content_record.last_api_status = status
    log.api_crawled = datetime.now(UTC)
    if status == 200:
        content_record.api_data = data
    content_record.save()
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
                    content_id=OuterRef("content_id"),
                    ingested=False,
                )
            )
        ),
        Show.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("content_id"),
                    ingested=False,
                )
            )
        ),
        Special.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("content_id"),
                    ingested=False,
                )
            )
        ),
        Season.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("content_id"),
                    ingested=False,
                )
            )
        ),
        Episode.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("content_id"),
                    ingested=False,
                )
            )
        ),
        Asset.objects.filter(
            Exists(
                ChangeLog.objects.filter(
                    content_id=OuterRef("content_id"),
                    ingested=False,
                )
            )
        ),
    ]
    for queryset in filter(lambda qs: qs.exists(), querysets):
        ChangeLog.objects.filter(
            content_id__in=queryset.values_list("content_id")
        ).update(ingested=True)


def realize_provisional_objects():
    """
    For any provisional objects, we try to find matching Changelog entries and
    send the API data into the realize method.
    """
    realized_shows = []
    for show in Show.objects.filter(provisional=True):
        try:
            changelog = ShowChangeLog.objects.get(
                title=show.title,
                deleted__isnull=True,
            )
            show.mm_content = changelog.mm_content
            show.provisional = False
            realized_shows.append(show)
        except ShowChangeLog.DoesNotExist:
            continue

    realized_seasons = []
    for season in Season.objects.filter(provisional=True).select_related("show"):
        try:
            changelog = SeasonChangeLog.objects.get(
                show_content_id=season.show.content_id,
                ordinal=season.ordinal,
                deleted__isnull=True,
            )
            season.mm_content = changelog.mm_content
            season.provisional = False
            realized_seasons.append(season)
        except SeasonChangeLog.DoesNotExist:
            continue

    for episode in Episode.objects.filter(provisional=True).select_related("season"):
        try:
            changelog = EpisodeChangeLog.objects.get(
                season_content_id=episode.season.content_id,
                ordinal=episode.ordinal,
                deleted__isnull=True,
            )
            episode.provisional = False
            episode.mm_content = changelog.mm_content
            episode.save(skip_ingest=True)
        except EpisodeChangeLog.DoesNotExist:
            continue

    for special in Special.objects.filter(
        provisional=True,
    ).select_related("show"):
        try:
            changelog = SpecialChangeLog.objects.get(
                show_content_id=special.show.content_id,
                title=special.title,
                deleted__isnull=True,
            )
            special.mm_content = changelog.mm_content
            special.provisional = False
            special.save(skip_ingest=True)

        except SpecialChangeLog.DoesNotExist:
            continue

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
    # for changelogs without API data (deleted objects would 404)

    logs = ChangeLog.objects.filter(
        mm_content__last_api_status__isnull=True,
        ingested=False,
        mm_content__deleted__isnull=True,
    )
    if logs.count() > limit:
        logs = logs[:limit]
        limit = 0
    else:
        limit = limit - logs.count()
    fetch_api_data.map(logs)

    # Since asset changes do not always result in the parent object reflecting
    # the change in the changelog, we have to get full data for any asset that
    # was already ingested before we started scraping the changelog
    asset_logs = AssetChangeLog.objects.filter(
        ingested=True,
        mm_content__last_api_status__isnull=True,
        mm_content__deleted__isnull=True,
    )
    if asset_logs.count() > limit:
        asset_logs = asset_logs[:limit]
        limit = 0
    else:
        limit = limit - asset_logs.count()
    fetch_api_data.map(asset_logs)

    # retry API fetch for objects that previously returned 403 or 404,
    # and which have been updated since the last API fetch attempt
    if limit > 0:
        logs = ChangeLog.objects.filter(
            mm_content__last_api_status__in=[403, 404],
            mm_content__deleted__isnull=True,
        ).filter(
            LessThan(
                F("api_crawled"),
                F("latest_timestamp"),
            )
        )

        if logs.count() > limit:
            logs = logs[:limit]

        fetch_api_data.map(logs)

    realize_provisional_objects()


def get_new_mm_changelogs():
    most_recent_entry = ChangeLog.objects.last()
    assert most_recent_entry is not None
    assert most_recent_entry.latest_timestamp is not None
    # rewind 5 minutes to account for changelog entries added since
    # last crawl
    delta = datetime.now(UTC) - most_recent_entry.latest_timestamp
    if delta.days > 30:
        urls = [f"{BASE_CHANGELOG_URL}&page={i}" for i in range(1, MAX_QUERIES)]
    else:
        since = datetime.strftime(
            most_recent_entry.latest_timestamp - timedelta(minutes=5),
            DT_FORMAT,
        )
        base_url = f"{BASE_CHANGELOG_URL}&since={since}"
        _, mm_response_data = get_PBSMM_record(base_url)
        last_page = max_page_number(mm_response_data)
        if last_page > MAX_QUERIES:  # add the bounds to Huey for processing
            urls = [f"{base_url}&page={i}" for i in range(1, MAX_QUERIES + 1)]
            changelog_bounds = {
                "lower_bound": MAX_QUERIES + 1,
                "upper_bound": last_page,
                "url": base_url,
            }
            HUEY.put("changelog_bounds", changelog_bounds)
        else:
            urls = [f"{base_url}&page={i}" for i in range(1, last_page + 1)]

    return urls


@db_periodic_task(crontab(minute="*/1"))
@lock_task("changelog-ingest")
def scrape_changelog():
    if not ChangeLog.objects.exists():
        # first time scraping, get first 400 pages
        urls = [f"{BASE_CHANGELOG_URL}&page={i}" for i in range(1, MAX_QUERIES)]
    elif HUEY.get("changelog_bounds", peek=True):  # process new batch of 400
        changelog_bounds = HUEY.get("changelog_bounds", peek=True)
        upper_bound = changelog_bounds["upper_bound"]
        lower_bound = changelog_bounds["lower_bound"]
        base_url = changelog_bounds["url"]
        bound_difference = upper_bound - lower_bound
        if bound_difference > 0:
            if bound_difference >= 400:
                new_lower_bound = lower_bound + MAX_QUERIES
                urls = [
                    f"{base_url}&page={i}" for i in range(lower_bound, new_lower_bound)
                ]
                changelog_bounds["lower_bound"] = new_lower_bound
            else:
                urls = [
                    f"{base_url}&page={i}" for i in range(lower_bound, upper_bound + 1)
                ]
                changelog_bounds["lower_bound"] = upper_bound
            HUEY.put("changelog_bounds", changelog_bounds)
        else:  # difference is 0
            HUEY.put(
                "changelog_bounds", None
            )  # get(peek=False) does not actually remove the key from storage
            urls = get_new_mm_changelogs()
    else:
        urls = get_new_mm_changelogs()

    entries = get_changelog_entries.map(urls)
    data = prep_changelog_data(chain.from_iterable(entries.get(blocking=True)))
    save_changelog_entries(data)
    set_ingested()

    remaining_api_calls = MAX_QUERIES - len(urls)
    get_changelog_data(remaining_api_calls)
