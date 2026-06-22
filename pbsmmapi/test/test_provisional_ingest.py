from unittest import mock
from uuid import UUID

from django.test import TestCase

from pbsmmapi.episode.models import Episode
from pbsmmapi.franchise.models import Franchise
from pbsmmapi.season.models import Season
from pbsmmapi.show.models import Show
from pbsmmapi.special.models import Special

FRANCHISE_ID = "f7062296-fa3d-4393-8b50-c0cac2db9a6d"
SHOW_ID = "adfb2f9d-f61e-4613-ac58-ab3bde582afb"
SEASON_ID = "08cd0667-88ae-4c3d-b726-c0833301f55b"
SPECIAL_ID = "2eb690f2-ebc4-41f6-9558-6962d8e43c48"
EPISODE_ID = "ac21bf4b-4930-4c0d-99af-a92fa2730274"

MMAPI_GET_URL = "pbsmmapi.api.api.requests.get"


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def mocked_requests_get(request_url, mmapi_response):
    def side_effect(*args, **kwargs):
        # returning a list for generic endpoint (/shows, /seasons, ...)
        if args and args[0] == request_url:
            return MockResponse({"links": {}, "data": mmapi_response}, 200)

        # returning one item for specific endpoints (/season/<season_id>,...)
        return MockResponse({"links": {}, "data": mmapi_response[0]}, 200)

    return side_effect


class ProvisionalIngestTestCase(TestCase):
    def test_provisional_season_is_realized_not_duplicated(self):
        seasons_url = "https://example.test/shows/nova/seasons/"
        show = Show(
            slug="nova",
            object_id=UUID(SHOW_ID),
            ingest_seasons=True,
            json={"links": {"seasons": seasons_url}},
        )
        show.save(skip_ingest=True)

        provisional = Season(
            show=show,
            show_api_id=UUID(SHOW_ID),
            ordinal=1,
            provisional=True,
        )
        provisional.save(skip_ingest=True)

        entries = [
            {
                "id": SEASON_ID,
                "type": "season",
                "attributes": {"ordinal": 1},
                "links": {},
            }
        ]

        with mock.patch(
            MMAPI_GET_URL, side_effect=mocked_requests_get(seasons_url, entries)
        ):
            show.process_seasons()

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(SEASON_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Season.objects.filter(object_id=UUID(SEASON_ID)).count(), 1)

    def test_provisional_special_is_realized_not_duplicated(self):
        specials_base = "https://example.test/shows/nova/specials/"
        specials_url = f"{specials_base}?platform-slug=partnerplayer"
        show = Show(
            slug="nova",
            object_id=UUID(SHOW_ID),
            ingest_specials=True,
            json={"links": {"specials": specials_base}},
        )
        show.save(skip_ingest=True)

        provisional = Special(
            slug="a-provisional-special",
            show=show,
            show_api_id=UUID(SHOW_ID),
            title="A Provisional Special",
            provisional=True,
        )
        provisional.save(skip_ingest=True)

        entries = [
            {
                "id": SPECIAL_ID,
                "type": "special",
                "attributes": {"title": "A Provisional Special"},
                "links": {},
            }
        ]

        with mock.patch(
            MMAPI_GET_URL, side_effect=mocked_requests_get(specials_url, entries)
        ):
            show.process_specials()

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(SPECIAL_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Special.objects.filter(object_id=UUID(SPECIAL_ID)).count(), 1)

    def test_provisional_episode_is_realized_not_duplicated(self):
        episodes_url = "https://example.test/seasons/nova/episodes/"
        season = Season(
            object_id=UUID(SEASON_ID),
            ordinal=1,
            ingest_episodes=True,
        )
        season.save(skip_ingest=True)

        provisional = Episode(
            slug="a-provisional-episode",
            season=season,
            season_api_id=UUID(SEASON_ID),
            ordinal=1,
            provisional=True,
        )
        provisional.save(skip_ingest=True)

        entries = [
            {
                "id": EPISODE_ID,
                "type": "episode",
                "attributes": {"ordinal": 1},
                "links": {},
            }
        ]
        with mock.patch(
            MMAPI_GET_URL, side_effect=mocked_requests_get(episodes_url, entries)
        ):
            season.process_episodes(episodes_url)

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(EPISODE_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Episode.objects.filter(object_id=UUID(EPISODE_ID)).count(), 1)

    def test_provisional_show_is_realized_not_duplicated(self):
        shows_base = "https://example.test/shows/"
        shows_url = f"{shows_base}?platform-slug=partnerplayer"

        franchise = Franchise(
            slug="a-franchise",
            object_id=UUID(FRANCHISE_ID),
            ingest_shows=True,
            json={"links": {"shows": shows_base}},
        )
        franchise.save(skip_ingest=True)

        provisional = Show(
            slug="nova",
            title="NOVA",
            provisional=True,
        )
        provisional.save(skip_ingest=True)

        entries = [
            {
                "id": SHOW_ID,
                "type": "show",
                "attributes": {"title": "NOVA"},
                "links": {},
            }
        ]

        with mock.patch(
            MMAPI_GET_URL, side_effect=mocked_requests_get(shows_url, entries)
        ):
            franchise.process_shows()

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(SHOW_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Show.objects.filter(object_id=UUID(SHOW_ID)).count(), 1)
