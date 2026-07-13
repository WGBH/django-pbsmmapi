import json
import re
from unittest import mock
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase
from huey.contrib.djhuey import HUEY

from pbsmmapi.asset.models import Asset
from pbsmmapi.show.models import Show
from pbsmmapi.test.url_map import url_map

default_data_set = url_map
assets_deleted_data_set = url_map.copy()
assets_deleted_data_set[
    "https://media.services.pbs.org/api/v1/shows/adfb2f9d-f61e-4613-ac58-ab3bde582afb/assets/?platform-slug=partnerplayer"
] = "test_fixtures/nova_shows_adfb2f9d-f61e-4613-ac58-ab3bde582afb_assets_minus_one.json"
assets_deleted_data_set[
    "https://media.services.pbs.org/api/v1/seasons/7f613b59-588b-4ec5-bcb1-a3d595b2579c/assets/?platform-slug=partnerplayer"
] = "test_fixtures/nova_seasons_7f613b59-588b-4ec5-bcb1-a3d595b2579c_assets_minus_one.json"
assets_deleted_data_set[
    "https://media.services.pbs.org/api/v1/specials/a3410528-7f72-47e8-b28d-6861693b9309/assets/?platform-slug=partnerplayer"
] = "test_fixtures/nova_specials_a3410528-7f72-47e8-b28d-6861693b9309_assets_minus_one.json"
assets_deleted_data_set[
    "https://media.services.pbs.org/api/v1/episodes/107268fc-0437-4877-8c3b-d5fdcef32737/assets/?platform-slug=partnerplayer"
] = "test_fixtures/nova_episodes_107268fc-0437-4877-8c3b-d5fdcef32737_assets_minus_one.json"

data_set = default_data_set


def get_api_json(url):
    with open(data_set[url], "r") as data_file:
        return json.load(data_file)


# The ingest re-fetches every asset one-by-one at .../api/v1/assets/<uuid>/,
# but the fixtures only mock the .../assets/?... list endpoints. Each list item
# is already a full asset object, so serve the detail response synthesized from
# the list fixtures of the *currently selected* data_set (default vs the
# minus-one deleted set) instead of 404ing (which would leave slug='').
ASSET_DETAIL_RE = re.compile(r"/api/v1/assets/([0-9a-f-]{36})/")

# {id(data_set): {asset_id: asset object}} — cached per data_set so switching to
# assets_deleted_data_set rebuilds the index from its (minus-one) fixtures.
_asset_detail_cache = {}


def _asset_detail(asset_id):
    index = _asset_detail_cache.get(id(data_set))
    if index is None:
        index = {}
        for url, path in data_set.items():
            if "/assets/?" not in url:  # only the asset LIST fixtures
                continue
            try:
                with open(path, "r") as data_file:
                    data = json.load(data_file)
            except (OSError, ValueError):
                continue
            for item in data.get("data", []):
                if isinstance(item, dict) and item.get("id"):
                    index.setdefault(item["id"], item)
        _asset_detail_cache[id(data_set)] = index
    return index.get(asset_id)


class MockResponse:
    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data


def mocked_requests_get(*args, **kwargs):
    url = args[0]
    asset_match = ASSET_DETAIL_RE.search(url)
    if asset_match:
        item = _asset_detail(asset_match.group(1))
        if item is None:
            return MockResponse(None, 404)
        return MockResponse({"data": item, "links": item.get("links", {})}, 200)
    try:
        response = get_api_json(url)
        return MockResponse(response, 200)
    except KeyError:
        return MockResponse(None, 404)


class ShowIngestTestCase(TestCase):
    @mock.patch("pbsmmapi.api.api.requests.get", side_effect=mocked_requests_get)
    def setUp(self, mock_get):
        # The ingest cascade runs through post_save @db_task chains; run huey
        # inline so seasons/specials/episodes/assets are created synchronously
        # within the test (no consumer runs in the test environment). Scoped to
        # this class: capture and restore the prior immediate value so we never
        # leak state into other suites (rather than assuming it was False).
        original_immediate = HUEY.immediate
        self.addCleanup(setattr, HUEY, "immediate", original_immediate)
        HUEY.immediate = True
        try:
            Show.objects.get(slug="nova")
        except ObjectDoesNotExist:
            nova = Show()
            nova.slug = "nova"
            nova.ingest_on_save = True
            nova.ingest_seasons = True
            nova.ingest_specials = True
            nova.ingest_episodes = True
            nova.save()

    @mock.patch("pbsmmapi.api.api.requests.get", side_effect=mocked_requests_get)
    def reingest(
        self,
        mock_get,
        ingest_seasons=False,
        ingest_specials=False,
        ingest_episodes=False,
    ):
        nova = Show.objects.get(slug="nova")
        nova.ingest_seasons = ingest_seasons
        nova.ingest_specials = ingest_specials
        nova.ingest_episodes = ingest_episodes
        nova.ingest_on_save = True
        nova.save()

    @mock.patch("pbsmmapi.api.api.requests.get", side_effect=mocked_requests_get)
    def test_show_ingested(self, mock_get):
        nova = Show.objects.get(slug="nova")
        self.assertEqual(nova.content_id, UUID("adfb2f9d-f61e-4613-ac58-ab3bde582afb"))

    @mock.patch("pbsmmapi.api.api.requests.get", side_effect=mocked_requests_get)
    def test_show_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest()
        nova_show_asset = Asset.objects.get(slug="nova-switching-genes-on-and-off")
        self.assertEqual(
            nova_show_asset.content_id, UUID("bae3b21e-2465-4629-afce-1f192c7a11c9")
        )
        # delete_stale_assets is disabled everywhere, so an asset that drops out
        # of the parent's list is retained rather than pruned
        data_set = assets_deleted_data_set
        self.reingest()
        data_set = default_data_set
        self.assertTrue(
            Asset.objects.filter(slug="nova-switching-genes-on-and-off").exists()
        )

    @mock.patch("pbsmmapi.api.api.requests.get", side_effect=mocked_requests_get)
    def test_season_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest(ingest_seasons=True)
        landslides = Asset.objects.get(slug="predicting-landslides-qh7jt9")
        self.assertEqual(landslides.title, "Predicting Landslides")
        # delete_stale_assets is disabled everywhere, so the asset is retained
        data_set = assets_deleted_data_set
        self.reingest(ingest_seasons=True)
        self.assertTrue(
            Asset.objects.filter(slug="predicting-landslides-qh7jt9").exists()
        )

    @mock.patch("pbsmmapi.api.api.requests.get", side_effect=mocked_requests_get)
    def test_special_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest(ingest_specials=True)
        saturn = Asset.objects.get(slug="front-row-seat-saturn-0vf9j2")
        self.assertEqual(saturn.title, "Front Row Seat to Saturn")
        # delete_stale_assets is disabled everywhere, so the asset is retained
        data_set = assets_deleted_data_set
        self.reingest(ingest_specials=True)
        self.assertTrue(
            Asset.objects.filter(slug="front-row-seat-saturn-0vf9j2").exists()
        )

    @mock.patch("pbsmmapi.api.api.requests.get", side_effect=mocked_requests_get)
    def test_episode_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest(ingest_episodes=True, ingest_seasons=True)
        make_life = Asset.objects.get(slug="can-we-make-life-hquxsp")
        self.assertEqual(make_life.title, "Can We Make Life? Preview")
        # delete_stale_assets is disabled everywhere, so the asset is retained
        data_set = assets_deleted_data_set
        self.reingest(ingest_episodes=True, ingest_seasons=True)
        self.assertTrue(Asset.objects.filter(slug="can-we-make-life-hquxsp").exists())
