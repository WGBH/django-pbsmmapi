"""
Regression tests for provisional-object realization during *standard* ingest.

Background
----------
Provisional objects are created with ``provisional=True`` and ``object_id=NULL``.
The standard ingest closures (``Show.process_seasons``/``process_specials``,
``Season.process_episodes`` and ``Franchise.process_shows``) key their
``*_or_create`` calls on ``object_id``. Because a provisional row has a NULL
``object_id`` it never matched, so a *second*, duplicate row was created with the
real UUID. Later, ``changelog.tasks.realize_provisional_objects`` tried to set
that same UUID on the provisional row and raised an ``IntegrityError`` on the
unique ``object_id`` constraint -- which halted the whole changelog pipeline.

The fix makes every standard ingest closure call ``realize()`` first, so an
existing provisional row is promoted in place (its ``object_id`` is set and
``provisional`` flipped to ``False``) instead of a duplicate being created.

These tests feed a single synthetic list page (containing the real UUID) into
each ``process_*`` method and assert that the pre-existing provisional row is
realized and that no duplicate is created.
"""

from unittest import mock
from uuid import UUID

from django.test import TestCase

from pbsmmapi.episode.models import Episode
from pbsmmapi.franchise.models import Franchise
from pbsmmapi.season.models import Season
from pbsmmapi.show.models import Show
from pbsmmapi.special.models import Special
from pbsmmapi.test.test_show_ingest import mocked_requests_get

# Real UUIDs whose detail endpoints exist in ``pbsmmapi/test/url_map.py`` so the
# follow-up ingest triggered by ``realize().save()`` resolves cleanly.
NOVA_ID = "adfb2f9d-f61e-4613-ac58-ab3bde582afb"
SEASON_ID = "08cd0667-88ae-4c3d-b726-c0833301f55b"
SPECIAL_ID = "2eb690f2-ebc4-41f6-9558-6962d8e43c48"
EPISODE_ID = "ac21bf4b-4930-4c0d-99af-a92fa2730274"

REQUESTS_GET = "pbsmmapi.api.api.requests.get"


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def list_response(list_url, entries):
    """
    Build a ``requests.get`` side effect that returns a single, non-paginated
    list page for ``list_url`` and otherwise delegates to the fixture-backed
    ``mocked_requests_get`` (so detail endpoints still resolve).
    """

    def side_effect(*args, **kwargs):
        if args and args[0] == list_url:
            return MockResponse({"links": {}, "data": entries}, 200)
        return mocked_requests_get(*args, **kwargs)

    return side_effect


class ProvisionalSeasonIngestTestCase(TestCase):
    """``Show.process_seasons`` realizes a provisional Season in place."""

    def test_provisional_season_is_realized_not_duplicated(self):
        seasons_url = "https://example.test/shows/nova/seasons/"
        show = Show(
            slug="nova",
            object_id=UUID(NOVA_ID),
            ingest_seasons=True,
            json={"links": {"seasons": seasons_url}},
        )
        show.save(skip_ingest=True)

        provisional = Season(
            show=show,
            show_api_id=UUID(NOVA_ID),
            ordinal=46,
            provisional=True,
        )
        provisional.save(skip_ingest=True)

        entries = [
            {
                "id": SEASON_ID,
                "type": "season",
                "attributes": {"ordinal": 46},
                "links": {},
            }
        ]
        with mock.patch(REQUESTS_GET, side_effect=list_response(seasons_url, entries)):
            show.process_seasons()

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(SEASON_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Season.objects.filter(object_id=UUID(SEASON_ID)).count(), 1)


class ProvisionalSpecialIngestTestCase(TestCase):
    """``Show.process_specials`` realizes a provisional Special in place."""

    def test_provisional_special_is_realized_not_duplicated(self):
        specials_base = "https://example.test/shows/nova/specials/"
        specials_url = f"{specials_base}?platform-slug=partnerplayer"
        show = Show(
            slug="nova",
            object_id=UUID(NOVA_ID),
            ingest_specials=True,
            json={"links": {"specials": specials_base}},
        )
        show.save(skip_ingest=True)

        provisional = Special(
            slug="a-provisional-special",
            show=show,
            show_api_id=UUID(NOVA_ID),
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
        with mock.patch(REQUESTS_GET, side_effect=list_response(specials_url, entries)):
            show.process_specials()

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(SPECIAL_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Special.objects.filter(object_id=UUID(SPECIAL_ID)).count(), 1)


class ProvisionalEpisodeIngestTestCase(TestCase):
    """``Season.process_episodes`` realizes a provisional Episode in place."""

    def test_provisional_episode_is_realized_not_duplicated(self):
        episodes_url = "https://example.test/seasons/nova/episodes/"
        season = Season(
            object_id=UUID(SEASON_ID),
            ordinal=46,
            ingest_episodes=True,
        )
        season.save(skip_ingest=True)

        provisional = Episode(
            slug="a-provisional-episode",
            season=season,
            season_api_id=UUID(SEASON_ID),
            ordinal=2,
            provisional=True,
        )
        provisional.save(skip_ingest=True)

        entries = [
            {
                "id": EPISODE_ID,
                "type": "episode",
                "attributes": {"ordinal": 2},
                "links": {},
            }
        ]
        with mock.patch(REQUESTS_GET, side_effect=list_response(episodes_url, entries)):
            season.process_episodes(episodes_url)

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(EPISODE_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Episode.objects.filter(object_id=UUID(EPISODE_ID)).count(), 1)


class ProvisionalShowIngestTestCase(TestCase):
    """``Franchise.process_shows`` realizes a provisional Show in place."""

    def test_provisional_show_is_realized_not_duplicated(self):
        shows_base = "https://example.test/franchises/nova/shows/"
        shows_url = f"{shows_base}?platform-slug=partnerplayer"
        # Franchise.save() has no skip_ingest path; its detail endpoint is not in
        # url_map so the ingest 404-noops and the row is created untouched.
        with mock.patch(REQUESTS_GET, side_effect=mocked_requests_get):
            franchise = Franchise(
                slug="a-franchise",
                object_id=UUID("11111111-1111-1111-1111-111111111111"),
                ingest_shows=True,
                json={"links": {"shows": shows_base}},
            )
            franchise.save()

        provisional = Show(
            slug="nova",
            title="NOVA",
            provisional=True,
        )
        provisional.save(skip_ingest=True)

        entries = [
            {
                "id": NOVA_ID,
                "type": "show",
                "attributes": {"title": "NOVA"},
                "links": {},
            }
        ]
        with mock.patch(REQUESTS_GET, side_effect=list_response(shows_url, entries)):
            franchise.process_shows()

        provisional.refresh_from_db()
        self.assertEqual(provisional.object_id, UUID(NOVA_ID))
        self.assertFalse(provisional.provisional)
        self.assertEqual(Show.objects.filter(object_id=UUID(NOVA_ID)).count(), 1)
