from importlib import import_module
from unittest import mock
from uuid import UUID

from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import TestCase
from huey.contrib.djhuey import HUEY

from pbsmmapi.asset.models import Asset
from pbsmmapi.episode.models import Episode
from pbsmmapi.record.models import ContentRecord
from pbsmmapi.season.models import Season
from pbsmmapi.show.models import Show

SHOW_ID = "adfb2f9d-f61e-4613-ac58-ab3bde582afb"
SEASON_ID = "08cd0667-88ae-4c3d-b726-c0833301f55b"
EPISODE_ID = "ac21bf4b-4930-4c0d-99af-a92fa2730274"
ASSET_ID = "bae3b21e-2465-4629-afce-1f192c7a11c9"
EMPTY_EPISODE_ID = "107268fc-0437-4877-8c3b-d5fdcef32737"
NULL_TITLE_EPISODE_ID = "3f1c2b7e-9d4a-4c1e-8b2f-6a7d9e0c1b23"

MMAPI_GET_URL = "pbsmmapi.api.api.requests.Session.get"


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def payload(content_id, title, slug=None, ordinal=None):
    attributes = {"title": title}
    if slug is not None:
        attributes["slug"] = slug
    if ordinal is not None:
        attributes["ordinal"] = ordinal
    return {
        "data": {"id": content_id, "attributes": attributes},
        "links": {},
    }


def respond_with(data):
    return lambda *args, **kwargs: MockResponse(data, 200)


class TitleRefreshTestCase(TestCase):
    """
    A re-ingest must carry MM title changes onto the title column; slug stays
    as first ingested.
    """

    def setUp(self):
        original_immediate = HUEY.immediate
        self.addCleanup(setattr, HUEY, "immediate", original_immediate)
        HUEY.immediate = True

    def record(self, content_id, data):
        return ContentRecord.objects.create(
            content_id=UUID(content_id),
            api_data=data,
            last_api_status=200,
        )

    def test_episode_title_follows_mm(self):
        record = self.record(EPISODE_ID, payload(EPISODE_ID, "Old", "old-slug", 1))
        Episode(
            title="Old",
            slug="old-slug",
            ordinal=1,
            mm_content=record,
        ).save(skip_ingest=True)

        episode = Episode.objects.get(mm_content=record)
        new = payload(EPISODE_ID, "New", "new-slug", 1)
        with mock.patch(MMAPI_GET_URL, side_effect=respond_with(new)):
            episode.save()

        episode = Episode.objects.get(mm_content=record)
        self.assertEqual(episode.title, "New")
        self.assertEqual(episode.slug, "old-slug")

    def test_asset_title_follows_mm(self):
        record = self.record(ASSET_ID, payload(ASSET_ID, "Old", "old-asset"))
        Asset(title="Old", slug="old-asset", mm_content=record).save(skip_ingest=True)

        asset = Asset.objects.get(mm_content=record)
        new = payload(ASSET_ID, "New", "new-asset")
        with mock.patch(MMAPI_GET_URL, side_effect=respond_with(new)):
            asset.save()

        asset = Asset.objects.get(mm_content=record)
        self.assertEqual(asset.title, "New")
        self.assertEqual(asset.slug, "old-asset")

    def test_season_title_follows_mm(self):
        Show(slug="nova", title="NOVA").save(skip_ingest=True)
        show = Show.objects.get(slug="nova")
        record = self.record(SEASON_ID, payload(SEASON_ID, "Old", ordinal=1))
        Season(show=show, ordinal=1, title="Old", mm_content=record).save(
            skip_ingest=True
        )

        season = Season.objects.get(mm_content=record)
        new = payload(SEASON_ID, "New", ordinal=1)
        with mock.patch(MMAPI_GET_URL, side_effect=respond_with(new)):
            season.save()

        self.assertEqual(Season.objects.get(mm_content=record).title, "New")


class TitleBackfillTestCase(TestCase):
    def test_backfill_copies_payload_title(self):
        migration = import_module(
            "pbsmmapi.record.migrations.0003_backfill_titles_from_api_data"
        )
        drifted = ContentRecord.objects.create(
            content_id=UUID(EPISODE_ID),
            api_data=payload(EPISODE_ID, "New", "drifted", 1),
        )
        no_payload = ContentRecord.objects.create(
            content_id=UUID(EMPTY_EPISODE_ID),
            api_data={},
        )
        Episode(title="Old", slug="drifted", ordinal=1, mm_content=drifted).save(
            skip_ingest=True
        )
        Episode(title="Keep", slug="no-payload", ordinal=2, mm_content=no_payload).save(
            skip_ingest=True
        )
        null_title = ContentRecord.objects.create(
            content_id=UUID(NULL_TITLE_EPISODE_ID),
            api_data=payload(NULL_TITLE_EPISODE_ID, "From Null", "null-title", 3),
        )
        Episode(title=None, slug="null-title", ordinal=3, mm_content=null_title).save(
            skip_ingest=True
        )

        # the frozen models a migration receives, not the live ones
        apps = MigrationLoader(connection).project_state().apps
        migration.backfill_titles(apps, None)

        self.assertEqual(Episode.objects.get(mm_content=drifted).title, "New")
        self.assertEqual(Episode.objects.get(mm_content=no_payload).title, "Keep")
        self.assertEqual(Episode.objects.get(mm_content=null_title).title, "From Null")
