from io import StringIO
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

    def test_sync_skips_changelog_without_content_record(self):
        # a ChangeLog whose mm_content link is NULL (SET_NULL / legacy data)
        # must not drive the cascade: descendant_querysets(resource_type, None)
        # would match every object whose parent has a NULL record.
        ghost_show = Show(slug="ghost")
        ghost_show.save(skip_ingest=True)  # no linked ContentRecord
        victim = Season(show=ghost_show, ordinal=1, mm_content=make_record(SEASON_ID))
        victim.save(skip_ingest=True)

        # a "show" delete changelog whose record link was cleared
        log = make_changelog(SHOW_ID, {T1: "delete"})
        ChangeLog.objects.filter(pk=log.pk).update(mm_content=None)
        log = ChangeLog.objects.get(pk=log.pk)
        self.assertIsNone(log.mm_content_id)

        sync_deleted_state(log)

        # the unrelated season (parent show has a NULL record) is NOT marked
        self.assertIsNone(record_deleted(SEASON_ID))

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

    def test_undelete_keeps_descendants_of_still_deleted_intermediate(self):
        # restoring an ancestor must not resurrect objects under an
        # intermediate that is still deleted in its own right
        # (ancestor-deleted implies descendant-deleted).
        self.make_show_tree()
        # delete the whole subtree via the show
        show_log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(show_log)
        # the season is ALSO deleted on its own, later
        season_log = make_changelog(SEASON_ID, {T2: "delete"}, resource_type="season")
        sync_deleted_state(season_log)

        # restore the show
        show_log = ChangeLog.objects.get(pk=show_log.pk)
        show_log.entries[T3] = {"action": "update", "updated_fields": ["title"]}
        show_log.save()
        sync_deleted_state(show_log)

        # the show and its directly-cascaded descendants come back alive
        for content_id in (SHOW_ID, SPECIAL_ID, SHOW_ASSET_ID):
            self.assertIsNone(record_deleted(content_id))
        # the season stays deleted (its own delete) ...
        self.assertEqual(record_deleted(SEASON_ID), parse_changelog_timestamp(T2))
        # ... and so does everything under the still-deleted season
        self.assertEqual(record_deleted(EPISODE_ID), parse_changelog_timestamp(T2))
        self.assertEqual(
            record_deleted(EPISODE_ASSET_ID), parse_changelog_timestamp(T2)
        )

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

    def test_force_reingest_undeletes(self):
        show, *_ = self.make_show_tree()
        # episode_asset was deleted in its own right; it must survive the override
        asset_log = make_changelog(
            EPISODE_ASSET_ID, {T0: "delete"}, resource_type="asset"
        )
        sync_deleted_state(asset_log)
        # deleting the show cascades delete marks to the whole subtree
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)

        with mock.patch(MMAPI_GET_URL, side_effect=mocked_requests_get) as mock_get:
            show_admin = PBSMMShowAdmin(Show, django_admin.site)
            show_admin.force_reingest(None, Show.objects.filter(pk=show.pk))

        # the show AND its cascade-marked descendants are cleared
        for content_id in (SHOW_ID, SEASON_ID, EPISODE_ID, SPECIAL_ID, SHOW_ASSET_ID):
            self.assertIsNone(record_deleted(content_id))
        # the individually deleted asset keeps its own timestamp
        self.assertEqual(
            record_deleted(EPISODE_ASSET_ID), parse_changelog_timestamp(T0)
        )
        # the show's ChangeLog mirror is cleared and reingest ran
        log.refresh_from_db()
        self.assertIsNone(log.deleted)
        mock_get.assert_called()

    def test_force_reingest_reingests_with_stale_cached_mm_content(self):
        # the admin may hand force_reingest an instance whose mm_content
        # relation was already cached (select_related / deleted_flag render),
        # holding a stale non-NULL deleted; the override must still ingest.
        show = self.make_show()
        log = make_changelog(SHOW_ID, {T1: "delete"})
        sync_deleted_state(log)

        # cache the relation with the stale (deleted) value
        item = Show.objects.select_related("mm_content").get(pk=show.pk)
        self.assertIsNotNone(item.deleted)

        with mock.patch(MMAPI_GET_URL, side_effect=mocked_requests_get) as mock_get:
            show_admin = PBSMMShowAdmin(Show, django_admin.site)
            show_admin.force_reingest(None, [item])

        # ingest was attempted (not skipped on the stale cache) and the mark
        # is cleared
        mock_get.assert_called()
        self.assertIsNone(record_deleted(SHOW_ID))

    def test_get_changelog_data_skips_deleted_logs(self):
        # cascade-deleted: the ContentRecord is marked (via an ancestor's
        # delete) while this changelog's own mirror stays NULL — it must still
        # be excluded from the API fetch.
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
            mock.patch("pbsmmapi.changelog.tasks.fetch_api_data") as mock_fetch,
            mock.patch("pbsmmapi.changelog.tasks.realize_provisional_objects"),
        ):
            get_changelog_data(10)

        fetched_ids = [
            log.mm_content_id
            for call in mock_fetch.map.call_args_list
            for log in call.args[0]
        ]
        self.assertNotIn(deleted_log.mm_content_id, fetched_ids)
        self.assertIn(live_log.mm_content_id, fetched_ids)

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

    def test_backfill_deleted_command(self):
        self.make_show()
        self.make_show(slug="nature", content_id=SHOW2_ID)
        make_changelog(SHOW_ID, {T1: "update", T2: "delete"})
        make_changelog(SHOW2_ID, {T1: "delete", T2: "update"})

        out = StringIO()
        call_command("backfill_deleted", stdout=out)

        self.assertEqual(record_deleted(SHOW_ID), parse_changelog_timestamp(T2))
        self.assertIsNone(record_deleted(SHOW2_ID))
        # the in-memory counter matches reality: only SHOW_ID's latest entry is
        # a delete, so exactly one changelog is reported marked
        self.assertIn("1 changelog(s) marked deleted", out.getvalue())
