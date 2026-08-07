from importlib import import_module
import json
import os
import re
from unittest import mock
from uuid import UUID

from django.apps import apps
from django.contrib import admin as django_admin
from django.db import (
    IntegrityError,
    transaction,
)
from django.test import (
    TestCase,
    override_settings,
)

from pbsmmapi.abstract.helpers import parse_changelog_timestamp
from pbsmmapi.asset.models import Asset
from pbsmmapi.changelog.models import ChangeLog
from pbsmmapi.changelog.tasks import (
    MediaManagerError,
    fetch_pbsmm_record,
    get_changelog_data,
    mark_deleted,
    reingest_updated_objects,
    save_changelog_entries,
    sync_deleted_state,
)
from pbsmmapi.episode.models import Episode
from pbsmmapi.record.models import ContentRecord
from pbsmmapi.season.models import Season
from pbsmmapi.show.admin import PBSMMShowAdmin
from pbsmmapi.show.models import Show
from pbsmmapi.show.tasks import scrape_media_manager_shows
from pbsmmapi.special.models import Special
from pbsmmapi.test.url_map import url_map

# the module name starts with a digit, so it needs importlib instead of a
# plain import statement
backfill_migration = import_module(
    "pbsmmapi.changelog.migrations.0003_backfill_deleted"
)

SHOW_ID = "adfb2f9d-f61e-4613-ac58-ab3bde582afb"
SHOW2_ID = "0f6b1922-4c86-4ba4-b5ee-90701ec6b4b1"
SEASON_ID = "08cd0667-88ae-4c3d-b726-c0833301f55b"
SPECIAL_ID = "2eb690f2-ebc4-41f6-9558-6962d8e43c48"
EPISODE_ID = "ac21bf4b-4930-4c0d-99af-a92fa2730274"
SHOW_ASSET_ID = "5e36e35c-27a5-4bfa-b0dc-6a9b81b2fdc0"
EPISODE_ASSET_ID = "8a4b7c39-91e4-4a17-a2f4-2bfcbd9a3f11"

MMAPI_GET_URL = "pbsmmapi.abstract.models.get_PBSMM_record"

T0 = "2027-01-01T00:00:00.000000Z"
T1 = "2027-01-02T00:00:00.000000Z"
T2 = "2027-01-03T00:00:00.000000Z"
T3 = "2027-01-04T00:00:00.000000Z"
T4 = "2027-01-05T00:00:00.000000Z"


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ASSET_DETAIL_RE = re.compile(r"/api/v1/assets/([0-9a-f-]{36})/")
_asset_detail_cache = {}


def _asset_detail(asset_id):
    index = _asset_detail_cache.get(id(url_map))
    if index is None:
        index = {}
        for url, path in url_map.items():
            if "/assets/?" not in url:
                continue
            if not os.path.isabs(path):
                path = os.path.join(BASE_DIR, path)
            try:
                with open(path, "r") as data_file:
                    data = json.load(data_file)
            except (OSError, ValueError):
                continue
            for item in data.get("data", []):
                if isinstance(item, dict) and item.get("id"):
                    index.setdefault(item["id"], item)
        _asset_detail_cache[id(url_map)] = index
    return index.get(asset_id)


def mocked_requests_get(url, *args, **kwargs):
    asset_match = ASSET_DETAIL_RE.search(url)
    if asset_match:
        item = _asset_detail(asset_match.group(1))
        if item is None:
            return 404, {}
        return 200, {"data": item, "links": item.get("links", {})}
    try:
        fixture_path = url_map[url]
        if not os.path.isabs(fixture_path):
            fixture_path = os.path.join(BASE_DIR, fixture_path)
        with open(fixture_path, "r") as data_file:
            return 200, json.load(data_file)
    except (KeyError, FileNotFoundError):
        return 404, {}


def make_record(content_id: str) -> ContentRecord:
    return ContentRecord.objects.create(content_id=UUID(content_id), api_data={})


def record_deleted(content_id: str):
    return ContentRecord.objects.get(pk=UUID(content_id)).deleted


def make_changelog(content_id, actions, resource_type="show"):
    # Every changelog owns a ContentRecord (THES-469); reuse an existing one
    # so a changelog and its content model share the same record.
    record, _ = ContentRecord.objects.get_or_create(content_id=UUID(content_id))
    log = ChangeLog(
        resource_type=resource_type,
        mm_content=record,
        entries={
            timestamp: {"action": action, "updated_fields": []}
            for timestamp, action in actions.items()
        },
    )
    log.save()
    return log


class ChangelogDeletedTestCase(TestCase):
    def make_show(self, slug="nova", content_id=SHOW_ID):
        show = Show(slug=slug, mm_content=make_record(content_id))
        show.save(skip_ingest=True)
        return show

    def make_show_tree(self):
        show = self.make_show()
        season = Season(
            show=show,
            ordinal=1,
            mm_content=make_record(SEASON_ID),
        )
        season.save(skip_ingest=True)
        episode = Episode(
            slug="an-episode",
            season=season,
            ordinal=1,
            mm_content=make_record(EPISODE_ID),
        )
        episode.save(skip_ingest=True)
        special = Special(
            slug="a-special",
            show=show,
            title="A Special",
            mm_content=make_record(SPECIAL_ID),
        )
        special.save(skip_ingest=True)
        # skip_ingest: a plain save() would hit the API and run set_parent(),
        # which clears the parent FKs when api_data has no parent_tree
        show_asset = Asset(
            slug="a-show-asset",
            show=show,
            mm_content=make_record(SHOW_ASSET_ID),
        )
        show_asset.save(skip_ingest=True)
        episode_asset = Asset(
            slug="an-episode-asset",
            episode=episode,
            mm_content=make_record(EPISODE_ASSET_ID),
        )
        episode_asset.save(skip_ingest=True)
        return show, season, episode, special, show_asset, episode_asset

    def test_delete_entry_marks_record(self):
        self.make_show()
        combined = {
            SHOW_ID: {
                "resource_type": "show",
                "changelogs": {
                    T1: {"action": "update", "updated_fields": ["title"]},
                    T2: {"action": "delete", "updated_fields": []},
                },
            }
        }
        save_changelog_entries.call_local(combined)

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T2))

    def test_newer_update_does_not_clear_deleted(self):
        # deletes are terminal: recreation gets a new content ID and unpublish
        # arrives as an update, so a newer entry on the same ID never revives
        # the record
        self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T1))

        log = ChangeLog.objects.get(pk=log.pk)
        log.entries[T2] = {"action": "update", "updated_fields": ["title"]}
        log.save()
        sync_deleted_state(log)

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T1))

    def test_latest_entry_wins(self):
        self.make_show()
        log = make_changelog(
            SHOW_ID,
            {T1: "update", T2: "delete", T3: "update", T4: "delete"},
        )
        sync_deleted_state(log)
        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T4))

    def test_batch_delete_records_latest_delete(self):
        # several entries arrive in ONE batch (backfill / merged scrape):
        # the recorded time is the most recent delete
        self.make_show()
        log = make_changelog(SHOW_ID, {T1: "update", T2: "delete", T4: "delete"})
        sync_deleted_state(log)

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T4))

    def test_latest_entry_is_chronological_not_lexicographic(self):
        # a microsecond-bearing timestamp is chronologically LATER but sorts
        # BEFORE the plain one as a string ('.' < 'Z'); the delete must win.
        no_micro_update = "2027-01-01T00:00:00Z"
        later_micro_delete = "2027-01-01T00:00:00.000001Z"
        self.assertGreater(no_micro_update, later_micro_delete)  # lexicographic trap
        self.assertGreater(  # but chronologically the delete is later
            parse_changelog_timestamp(later_micro_delete),
            parse_changelog_timestamp(no_micro_update),
        )
        self.make_show()
        log = make_changelog(
            SHOW_ID, {no_micro_update: "update", later_micro_delete: "delete"}
        )
        sync_deleted_state(log)
        self.assertEqual(
            record_deleted(SHOW_ID), parse_changelog_timestamp(later_micro_delete)
        )

    def test_latest_timestamp_is_chronological(self):
        # ChangeLog.save() also orders by instant, not string: the microsecond
        # entry is the later instant even though it sorts first as a string.
        expected = parse_changelog_timestamp("2027-01-01T00:00:00.000001Z")
        log = make_changelog(
            SHOW_ID,
            {
                "2027-01-01T00:00:00.000001Z": "update",
                "2027-01-01T00:00:00Z": "update",
            },
        )
        # in-memory value is the parsed datetime, not the raw string key
        self.assertEqual(log.latest_timestamp, expected)
        log.refresh_from_db()
        self.assertEqual(log.latest_timestamp, expected)

    def test_parse_changelog_timestamp_is_utc_aware(self):
        utc = parse_changelog_timestamp("2027-01-01T00:00:00Z")
        # a non-UTC offset normalizes to the same UTC instant
        self.assertEqual(parse_changelog_timestamp("2027-01-01T05:00:00+05:00"), utc)
        # a timestamp with no timezone is assumed UTC and comes back aware
        naive_input = parse_changelog_timestamp("2027-01-01T00:00:00")
        self.assertIsNotNone(naive_input.tzinfo)
        self.assertEqual(naive_input, utc)

    def test_newer_delete_overwrites_timestamp(self):
        self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T1))

        # more entries arrive in a later batch, ending in a fresh delete
        log = ChangeLog.objects.get(pk=log.pk)
        log.entries[T2] = {"action": "update", "updated_fields": ["title"]}
        log.entries[T3] = {"action": "delete", "updated_fields": []}
        log.save()
        sync_deleted_state(log)

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T3))

    def test_repeated_delete_records_latest(self):
        # every delete is recorded, even when the caller holds a stale
        # instance (all writes are overwrites)
        self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        mark_deleted(log, parse_changelog_timestamp(T2))

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T2))

    def test_missing_content_model_still_marks_record(self):
        # THES-469 gives every changelog a ContentRecord even when the content
        # model (Show/Season/...) was never ingested: the record gets marked,
        # but no Show row exists.
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T1))
        self.assertFalse(Show.objects.exists())

    def test_mm_content_cannot_be_null(self):
        # the schema forbids a ChangeLog without a ContentRecord, so code paths
        # need no NULL-mm_content safeguards (a NULL link used to make
        # mark_deleted's asset filter match every asset of a record-less show)
        log = make_changelog(SHOW_ID, {T1: "delete"})
        with self.assertRaises(IntegrityError), transaction.atomic():
            ChangeLog.objects.filter(pk=log.pk).update(mm_content=None)

    def test_delete_marks_object_and_direct_assets_only(self):
        self.make_show_tree()

        log = make_changelog(SHOW_ID, {T2: "delete"})
        sync_deleted_state(log)

        # the object and its directly-attached assets record the delete
        deleted_at = parse_changelog_timestamp(T2)
        self.assertEqual(record_deleted(SHOW_ID), deleted_at)
        self.assertEqual(record_deleted(SHOW_ASSET_ID), deleted_at)
        # every other type gets its own PBS delete entry (children are deleted
        # before parents), so nothing else is flagged — the episode's asset
        # belongs to the episode's own cascade
        for content_id in (SEASON_ID, EPISODE_ID, SPECIAL_ID, EPISODE_ASSET_ID):
            self.assertIsNone(record_deleted(content_id))

    def test_save_does_not_ingest_deleted(self):
        show = self.make_show()
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(
            deleted=parse_changelog_timestamp(T1)
        )
        show = Show.objects.get(pk=show.pk)  # fresh relation cache
        show.ingest_on_save = True
        with mock.patch(MMAPI_GET_URL) as mock_get:
            show.save()
        mock_get.assert_not_called()

    def test_deleted_asset_save_does_not_ingest(self):
        # Asset.save() unconditionally calls pre_save() -> process(); a deleted
        # asset must skip ingest and not crash on the unpack contract.
        record = make_record(SHOW_ASSET_ID)
        ContentRecord.objects.filter(pk=record.pk).update(
            deleted=parse_changelog_timestamp(T1)
        )
        asset = Asset(
            slug="an-asset",
            mm_content=ContentRecord.objects.get(pk=record.pk),
        )
        with mock.patch(MMAPI_GET_URL) as mock_get:
            asset.save()
            # process() must return a 2-tuple (not None) so pre_save can unpack
            self.assertEqual(asset.process(), (None, None))
        mock_get.assert_not_called()

    def test_pre_save_non_200_preserves_concurrent_delete(self):
        # Regression: Ingest.pre_save's non-200 branch must not resurrect a
        # record deleted mid-fetch. It used to full-save mm_content from a
        # snapshot taken before the (slow) API call, so a 404 that races the
        # object's own changelog delete un-tombstoned it; the write is now
        # scoped to last_api_status.
        show = self.make_show()  # keep the stale instance: mm_content.deleted None

        # a concurrent changelog delete stamps the record in the DB while the
        # instance above still holds deleted=None
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(
            deleted=parse_changelog_timestamp(T1)
        )

        # the object's own ingest fetch races and 404s (it is gone upstream)
        with mock.patch(
            "pbsmmapi.abstract.models.get_PBSMM_record", return_value=(404, None)
        ):
            self.assertEqual(show.pre_save(), 404)

        record = ContentRecord.objects.get(pk=UUID(SHOW_ID))
        self.assertEqual(record.deleted, parse_changelog_timestamp(T1))  # preserved
        self.assertEqual(record.last_api_status, 404)  # the only field written

    def test_force_reingest_reingests(self):
        show = self.make_show()

        with mock.patch(MMAPI_GET_URL, side_effect=mocked_requests_get) as mock_get:
            show_admin = PBSMMShowAdmin(Show, django_admin.site)
            show_admin.force_reingest(None, Show.objects.filter(pk=show.pk))

        mock_get.assert_called()

    def test_force_reingest_skips_deleted(self):
        # deletes are terminal — there is no un-delete override; the admin
        # action just saves, and save()'s ingest guard skips deleted objects
        show = self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)

        with mock.patch(MMAPI_GET_URL) as mock_get:
            show_admin = PBSMMShowAdmin(Show, django_admin.site)
            show_admin.force_reingest(None, Show.objects.filter(pk=show.pk))

        mock_get.assert_not_called()
        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T1))

    def test_get_changelog_data_skips_deleted_logs(self):
        # the ContentRecord is marked deleted (e.g. flagged by a parent's
        # delete cascade) — the log must be excluded from the API fetch.
        deleted_log = make_changelog(SHOW_ID, {T1: "update"})
        ChangeLog.objects.filter(pk=deleted_log.pk).update(
            api_crawled=parse_changelog_timestamp(T0),
        )
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(
            deleted=parse_changelog_timestamp(T1),
            last_api_status=404,
        )
        live_log = make_changelog(SHOW2_ID, {T2: "update"})

        with (
            mock.patch("pbsmmapi.changelog.tasks.fetch_pbsmm_record") as mock_fetch,
            mock.patch("pbsmmapi.changelog.tasks.realize_provisional_objects"),
        ):
            mock_fetch.map.return_value.get.return_value = [(200, {})]
            get_changelog_data()

        fetched_urls = [
            url for call in mock_fetch.map.call_args_list for url in call.args[0]
        ]
        self.assertNotIn(deleted_log.api_url, fetched_urls)
        self.assertIn(live_log.api_url, fetched_urls)

    def test_get_changelog_data_updates_record(self):
        # get_changelog_data updates last_api_status/api_data/api_crawled
        log = make_changelog(SHOW_ID, {T1: "update"})
        api_data = {"data": {"id": SHOW_ID, "attributes": {}}}

        with mock.patch(
            "pbsmmapi.changelog.tasks.get_PBSMM_record", return_value=(200, api_data)
        ):
            get_changelog_data()

        record = ContentRecord.objects.get(pk=UUID(SHOW_ID))
        self.assertEqual(record.last_api_status, 200)
        self.assertEqual(record.api_data, api_data)
        log.refresh_from_db()
        self.assertIsNotNone(log.api_crawled)
        self.assertEqual(list(log.entries.keys()), [T1])

    def test_fetch_pbsmm_record_5xx_raises_exception(self):
        with mock.patch(
            "pbsmmapi.changelog.tasks.get_PBSMM_record", return_value=(500, {})
        ):
            with self.assertRaises(MediaManagerError):
                fetch_pbsmm_record.call_local("http://example.com/api/")

    def test_fetch_pbsmm_record_returns_status_and_data(self):
        api_data = {"data": {"id": SHOW_ID, "attributes": {}}}
        with mock.patch(
            "pbsmmapi.changelog.tasks.get_PBSMM_record", return_value=(200, api_data)
        ):
            status, data = fetch_pbsmm_record.call_local("http://example.com/api/")
        self.assertEqual(status, 200)
        self.assertEqual(data, api_data)

    def test_reingest_skips_deleted_objects(self):
        # reingest_updated_objects (restored from rc_1.4.0) must not touch a
        # deleted object: it is excluded from the reingest querysets up front.
        show = self.make_show()  # ingested; date_last_api_update is NULL
        # a changelog newer than the last ingest — would trigger reingest...
        make_changelog(SHOW_ID, {T2: "update"})
        # ...but the object is deleted
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(
            deleted=parse_changelog_timestamp(T1)
        )

        with mock.patch(MMAPI_GET_URL) as mock_get:
            reingest_updated_objects()

        # not re-fetched, still deleted, and never even flagged for ingest
        # (ingest_on_save stays False, proving it was excluded, not just guarded)
        mock_get.assert_not_called()
        self.assertIsNotNone(record_deleted(SHOW_ID))
        self.assertFalse(Show.objects.get(pk=show.pk).ingest_on_save)

    @override_settings(PBSMM_SHOW_SLUGS=["nova"])
    def test_scraper_skips_deleted_show(self):
        self.make_show()
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(
            deleted=parse_changelog_timestamp(T1)
        )

        with mock.patch(MMAPI_GET_URL) as mock_get:
            scrape_media_manager_shows.call_local()

        mock_get.assert_not_called()
        self.assertEqual(Show.objects.count(), 1)
        self.assertIsNotNone(record_deleted(SHOW_ID))

    def test_backfill_deleted_migration(self):
        # the data migration is exercised directly with the live app registry;
        # apps.get_model resolves the same way as with historical models
        self.make_show()
        self.make_show(slug="nature", content_id=SHOW2_ID)
        make_changelog(SHOW_ID, {T1: "update", T2: "delete"})
        make_changelog(SHOW2_ID, {T1: "delete", T2: "update"})

        backfill_migration.backfill_deleted(apps, None)

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T2))
        self.assertIsNone(record_deleted(SHOW2_ID))

    def test_backfill_recomputes_latest_timestamp(self):
        # a legacy row whose latest_timestamp was computed lexicographically:
        # the microsecond entry is chronologically latest but sorts first as a
        # string, so the old code stored the plain 'Z' instant. Backfill must
        # recompute it from entries (parsed-instant order).
        micro = "2027-01-01T00:00:00.000001Z"
        plain = "2027-01-01T00:00:00Z"
        log = make_changelog(SHOW_ID, {micro: "update", plain: "update"})
        # simulate the stale lexicographic value
        ChangeLog.objects.filter(pk=log.pk).update(
            latest_timestamp=parse_changelog_timestamp(plain)
        )

        backfill_migration.backfill_deleted(apps, None)

        log.refresh_from_db()
        self.assertEqual(log.latest_timestamp, parse_changelog_timestamp(micro))
