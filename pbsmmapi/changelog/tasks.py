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
    HUEY,
    db_periodic_task,
    db_task,
    lock_task,
    task,
)

from pbsmmapi.abstract.constants import PBSMM_BASE_URL
from pbsmmapi.abstract.helpers import parse_changelog_timestamp
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


ASSET_PARENT_TYPES = {"franchise", "show", "season", "episode", "special"}


def mark_deleted(log: ChangeLog, deleted_at: datetime):
    """
    Record a delete on the object's ContentRecord and its direct assets'
    records, overwriting any earlier value — ``deleted`` always holds the
    most recent delete reported. The overwrite is idempotent and safe for
    stale instances and concurrent runs, and queryset .update() means no
    save()/ingest side effects.

    Only directly-attached assets follow the parent's state: PBS reports
    deletes for every other object type individually (children are deleted
    before their parents), but a parent's assets never get their own
    changelog delete entries. Nested assets (e.g. episode assets under a
    show) are covered by their own parent's entry.

    The asset lookup deliberately uses the parent FK columns, not the
    ``parent_tree`` annotation: ``parent_tree`` lives in
    ``mm_content.api_data`` and only exists after a successful detail fetch,
    while the FK is set when the parent's ``process_assets`` creates the
    row. An asset stuck on 403 (out of its availability window) or one whose
    record has not been fetched yet has no ``parent_tree`` — filtering on it
    would let exactly those assets escape the delete mark. An asset whose
    own ``mm_content`` is NULL contributes a NULL to the ``pk__in``
    subquery, which matches no record — there is nothing to mark for it.
    """
    ContentRecord.objects.filter(pk=log.mm_content_id).update(deleted=deleted_at)
    if log.resource_type not in ASSET_PARENT_TYPES:
        return
    direct_asset_records = Asset.objects.filter(
        **{f"{log.resource_type}__mm_content_id": log.mm_content_id},
    ).values_list("mm_content_id", flat=True)
    ContentRecord.objects.filter(pk__in=direct_asset_records).update(
        deleted=deleted_at,
    )


def sync_deleted_state(log: ChangeLog):
    """
    Record the delete when the latest changelog entry action is "delete".
    Idempotent.

    A delete is terminal: recreating an object in the Media Manager Console
    produces a new content ID (a brand-new object here), and unpublishing
    arrives as an "update" action — so a delete entry is never superseded on
    the same content ID and there is no un-delete path.

    The ``max()`` is not recomputing ``latest_timestamp`` — it locates which
    ``entries`` key is the newest, so that entry's action can be read.
    ``entries`` is keyed by the raw timestamp strings exactly as PBS sent
    them, while ``log.latest_timestamp`` is a normalized datetime: it is not
    a dict key, and it cannot be turned back into one, because many
    spellings parse to the same instant (missing microseconds, different
    offsets) and we cannot know which one PBS used. Parsing each key also
    keeps the comparison chronological rather than lexicographic across
    those mixed formats.
    """
    timestamp = max(log.entries.keys(), default=None, key=parse_changelog_timestamp)
    if timestamp is None:
        return
    if log.entries[timestamp].get("action") == "delete":
        mark_deleted(log, parse_changelog_timestamp(timestamp))


@db_task(retries=3)
def save_changelog_entries(combined: dict):
    """
    Using unified dict returned from prep_changelog_data, save ChangeLog
    instances for each content ID extracted from the changelog endpoint.
    """
    for content_id, data in combined.items():
        try:
            # key off the unique mm_content relation (mm_content_id == the
            # ContentRecord pk == this content_id), not the derived content_id
            # annotation, which requires a JOIN
            log = ChangeLog.objects.get(mm_content_id=content_id)
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


@task(retries=2, retry_delay=10)
@HUEY.rate_limit("get-changelog-entries", limit=MAX_QUERIES, per=60, retry=False)
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
        last_page = 1
    return last_page


@db_task(retries=3, retry_delay=70)
@HUEY.rate_limit("fetch-api-data", limit=MAX_QUERIES, per=60, retry=False)
def fetch_api_data(log_pk):
    # Refetch fresh instead of trusting a snapshot from enqueue time: deletes
    # are marked by save_changelog_entries, a queued task like this one, so a
    # delete can land between enqueue and execution — bail then. Queryset
    # .update() writes only the fields this task owns, so concurrent changes
    # (entries, deleted) cannot be reverted by a full-row save.
    log = ChangeLog.objects.filter(
        pk=log_pk,
        mm_content__deleted__isnull=True,
    ).first()
    if log is None:
        return
    status, data = get_PBSMM_record(log.api_url)
    updates = {"last_api_status": status}
    if status == 200:
        updates["api_data"] = data
    ContentRecord.objects.filter(pk=log.mm_content_id).update(**updates)
    ChangeLog.objects.filter(pk=log_pk).update(api_crawled=datetime.now(UTC))


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
                mm_content__deleted__isnull=True,
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
                mm_content__deleted__isnull=True,
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
                mm_content__deleted__isnull=True,
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
                mm_content__deleted__isnull=True,
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


def reingest_updated_objects():
    """
    When new actions appear in the changelog, we need to trigger
    ingest of the related object to get everything in sync.

    Deleted objects are excluded up front (``mm_content__deleted__isnull=True``):
    a delete is the newest changelog entry, so they would otherwise match the
    "changelog newer than last ingest" check and get a pointless ``save()`` that
    the model's own delete guard then skips anyway.
    """
    querysets = [
        Franchise.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("content_id"))),
            mm_content__deleted__isnull=True,
        ),
        Show.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("content_id"))),
            mm_content__deleted__isnull=True,
        ),
        Special.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("content_id"))),
            mm_content__deleted__isnull=True,
        ),
        Season.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("content_id"))),
            mm_content__deleted__isnull=True,
        ),
        Episode.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("content_id"))),
            mm_content__deleted__isnull=True,
        ),
        Asset.objects.filter(
            Exists(ChangeLog.objects.filter(content_id=OuterRef("content_id"))),
            mm_content__deleted__isnull=True,
        ),
    ]
    for queryset in querysets:
        for item in queryset:
            try:
                changelog = ChangeLog.objects.get(content_id=item.content_id)
            except ChangeLog.DoesNotExist:
                continue
            if changelog.latest_timestamp and (
                item.date_last_api_update is None
                or changelog.latest_timestamp > item.date_last_api_update
            ):
                item.ingest_on_save = True
                item.save()


def get_changelog_data():
    """
    For ChangeLog objects we can't match with an ingested object, we
    need to fetch the API data in order to determine whether to ingest
    the object.
    """
    # for changelogs without API data (deleted objects would 404)
    no_data_logs = ChangeLog.objects.filter(
        mm_content__last_api_status__isnull=True,
        ingested=False,
        mm_content__deleted__isnull=True,
    ).values_list("pk", flat=True)

    # Since asset changes do not always result in the parent object reflecting
    # the change in the changelog, we have to get full data for any asset that
    # was already ingested before we started scraping the changelog
    asset_logs = AssetChangeLog.objects.filter(
        ingested=True,
        mm_content__last_api_status__isnull=True,
        mm_content__deleted__isnull=True,
    ).values_list("pk", flat=True)

    # retry API fetch for objects that previously returned 403 or 404,
    # and which have been updated since the last API fetch attempt
    errored_logs = (
        ChangeLog.objects.filter(
            mm_content__last_api_status__in=[403, 404],
            mm_content__deleted__isnull=True,
        )
        .filter(
            LessThan(
                F("api_crawled"),
                F("latest_timestamp"),
            )
        )
        .values_list("pk", flat=True)
    )
    result = fetch_api_data.map(no_data_logs.union(asset_logs).union(errored_logs))
    result.get(blocking=True)

    realize_provisional_objects()
    reingest_updated_objects()


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
        urls = [f"{base_url}&page={i}" for i in range(1, last_page + 1)]
    return urls


@db_periodic_task(crontab(minute="*/1"))
@lock_task("changelog-ingest")
def scrape_changelog():
    if not ChangeLog.objects.exists():
        # first time scraping, get all changelogs
        _, mm_response_data = get_PBSMM_record(BASE_CHANGELOG_URL)
        last_page = max_page_number(mm_response_data)
        urls = [f"{BASE_CHANGELOG_URL}&page={i}" for i in range(1, last_page + 1)]
    else:
        urls = get_new_mm_changelogs()

    entries = get_changelog_entries.map(urls)
    data = prep_changelog_data(chain.from_iterable(entries.get(blocking=True)))
    save_changelog_entries(data)
    set_ingested()

    get_changelog_data()
