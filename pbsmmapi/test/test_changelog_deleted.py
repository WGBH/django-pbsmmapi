import json
from unittest import mock
from uuid import UUID

from django.contrib import admin as django_admin
from django.core.management import call_command
from django.test import (
    TestCase,
    override_settings,
)

from pbsmmapi.asset.models import Asset
from pbsmmapi.changelog.models import ChangeLog
from pbsmmapi.changelog.tasks import (
    get_changelog_data,
    mark_deleted,
    parse_changelog_timestamp,
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

SHOW_ID = "adfb2f9d-f61e-4613-ac58-ab3bde582afb"
SHOW2_ID = "0f6b1922-4c86-4ba4-b5ee-90701ec6b4b1"
SEASON_ID = "08cd0667-88ae-4c3d-b726-c0833301f55b"
SPECIAL_ID = "2eb690f2-ebc4-41f6-9558-6962d8e43c48"
EPISODE_ID = "ac21bf4b-4930-4c0d-99af-a92fa2730274"
SHOW_ASSET_ID = "5e36e35c-27a5-4bfa-b0dc-6a9b81b2fdc0"
EPISODE_ASSET_ID = "8a4b7c39-91e4-4a17-a2f4-2bfcbd9a3f11"

MMAPI_GET_URL = "pbsmmapi.api.api.requests.get"

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


def mocked_requests_get(*args, **kwargs):
    try:
        with open(url_map[args[0]], "r") as data_file:
            return MockResponse(json.load(data_file), 200)
    except KeyError:
        return MockResponse(None, 404)


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
        show_asset = Asset(
            slug="a-show-asset",
            show=show,
            mm_content=make_record(SHOW_ASSET_ID),
        )
        show_asset.save()
        episode_asset = Asset(
            slug="an-episode-asset",
            episode=episode,
            mm_content=make_record(EPISODE_ASSET_ID),
        )
        episode_asset.save()
        return show, season, episode, special, show_asset, episode_asset

    def test_delete_entry_marks_object_and_changelog(self):
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
        log = ChangeLog.objects.get(content_id=UUID(SHOW_ID))
        self.assertEqual(log.deleted, parse_changelog_timestamp(T2))

    def test_newer_update_clears_deleted(self):
        self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        self.assertIsNotNone(record_deleted(SHOW_ID))

        # a later scrape merges a newer update entry; the log is always
        # refetched from the DB in production (save_changelog_entries)
        log = ChangeLog.objects.get(pk=log.pk)
        log.entries[T2] = {"action": "update", "updated_fields": ["title"]}
        log.save()
        sync_deleted_state(log)

        self.assertIsNone(record_deleted(SHOW_ID))
        log.refresh_from_db()
        self.assertIsNone(log.deleted)

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
        log.refresh_from_db()
        self.assertEqual(log.deleted, parse_changelog_timestamp(T4))

    def test_new_delete_after_restore_records_new_timestamp(self):
        self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T1))

        # a restore and a fresh delete arrive together in a later batch
        log = ChangeLog.objects.get(pk=log.pk)
        log.entries[T2] = {"action": "update", "updated_fields": ["title"]}
        log.entries[T3] = {"action": "delete", "updated_fields": []}
        log.save()
        sync_deleted_state(log)

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T3))
        log.refresh_from_db()
        self.assertEqual(log.deleted, parse_changelog_timestamp(T3))

    def test_repeated_delete_records_latest(self):
        # every delete is recorded; record and mirror always agree, even when
        # the caller holds a stale instance (all writes are overwrites)
        self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        mark_deleted(log, parse_changelog_timestamp(T2))

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T2))
        log.refresh_from_db()
        self.assertEqual(log.deleted, parse_changelog_timestamp(T2))

    def test_missing_content_model_still_marks_record_and_changelog(self):
        # THES-469 gives every changelog a ContentRecord even when the content
        # model (Show/Season/...) was never ingested: the record and mirror get
        # marked, but no Show row exists.
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)
        log.refresh_from_db()
        self.assertEqual(log.deleted, parse_changelog_timestamp(T1))
        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T1))
        self.assertFalse(Show.objects.exists())

    def test_cascade_marks_descendants(self):
        self.make_show_tree()
        # episode_asset was already deleted on its own, earlier
        asset_log = make_changelog(
            EPISODE_ASSET_ID, {T0: "delete"}, resource_type="asset"
        )
        sync_deleted_state(asset_log)

        log = make_changelog(SHOW_ID, {T2: "delete"})
        sync_deleted_state(log)

        # every layer records the latest delete, the cascade included
        deleted_at = parse_changelog_timestamp(T2)
        for content_id in (
            SHOW_ID,
            SEASON_ID,
            EPISODE_ID,
            SPECIAL_ID,
            SHOW_ASSET_ID,
            EPISODE_ASSET_ID,
        ):
            self.assertEqual(record_deleted(content_id), deleted_at)
        # the asset's own changelog mirror keeps its own deletion time
        asset_log.refresh_from_db()
        self.assertEqual(asset_log.deleted, parse_changelog_timestamp(T0))

    def test_undelete_resyncs_descendants_from_their_mirrors(self):
        self.make_show_tree()
        asset_log = make_changelog(
            EPISODE_ASSET_ID, {T0: "delete"}, resource_type="asset"
        )
        sync_deleted_state(asset_log)
        log = make_changelog(SHOW_ID, {T2: "delete"})
        sync_deleted_state(log)

        log = ChangeLog.objects.get(pk=log.pk)
        log.entries[T3] = {"action": "update", "updated_fields": ["title"]}
        log.save()
        sync_deleted_state(log)

        for content_id in (SHOW_ID, SEASON_ID, EPISODE_ID, SPECIAL_ID, SHOW_ASSET_ID):
            self.assertIsNone(record_deleted(content_id))
        # the individually deleted asset gets its own timestamp back from its
        # changelog mirror instead of being resurrected
        self.assertEqual(
            record_deleted(EPISODE_ASSET_ID), parse_changelog_timestamp(T0)
        )

    def test_reingest_skips_deleted_objects(self):
        self.make_show()
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(
            deleted=parse_changelog_timestamp(T1)
        )
        make_changelog(SHOW_ID, {T2: "update"})

        with mock.patch(MMAPI_GET_URL) as mock_get:
            reingest_updated_objects()

        mock_get.assert_not_called()
        show = Show.objects.get(slug="nova")
        self.assertFalse(show.ingest_on_save)

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

    def test_force_reingest_undeletes(self):
        show = self.make_show()
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(
            deleted=parse_changelog_timestamp(T1)
        )

        with mock.patch(MMAPI_GET_URL, side_effect=mocked_requests_get) as mock_get:
            show_admin = PBSMMShowAdmin(Show, django_admin.site)
            show_admin.force_reingest(None, Show.objects.filter(pk=show.pk))

        self.assertIsNone(record_deleted(SHOW_ID))
        mock_get.assert_called()

    def test_get_changelog_data_skips_deleted_logs(self):
        deleted_log = make_changelog(SHOW_ID, {T1: "delete"})
        ChangeLog.objects.filter(pk=deleted_log.pk).update(
            deleted=parse_changelog_timestamp(T1),
            api_crawled=parse_changelog_timestamp(T0),
        )
        ContentRecord.objects.filter(pk=UUID(SHOW_ID)).update(last_api_status=404)
        live_log = make_changelog(SHOW2_ID, {T2: "update"})

        with (
            mock.patch("pbsmmapi.changelog.tasks.fetch_api_data") as mock_fetch,
            mock.patch("pbsmmapi.changelog.tasks.realize_provisional_objects"),
            mock.patch("pbsmmapi.changelog.tasks.reingest_updated_objects"),
        ):
            get_changelog_data(10)

        fetched_ids = [
            log.mm_content_id
            for call in mock_fetch.map.call_args_list
            for log in call.args[0]
        ]
        self.assertNotIn(deleted_log.mm_content_id, fetched_ids)
        self.assertIn(live_log.mm_content_id, fetched_ids)

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

    def test_backfill_deleted_command(self):
        self.make_show()
        self.make_show(slug="nature", content_id=SHOW2_ID)
        make_changelog(SHOW_ID, {T1: "update", T2: "delete"})
        make_changelog(SHOW2_ID, {T1: "delete", T2: "update"})

        call_command("backfill_deleted")

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T2))
        self.assertIsNone(record_deleted(SHOW2_ID))
