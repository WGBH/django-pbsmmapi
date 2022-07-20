# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import unittest
from uuid import UUID
try:
    from unittest import mock
except ImportError:
    import mock

from django.core.exceptions import ObjectDoesNotExist

from pbsmmapi.episode.models import Asset
from pbsmmapi.show.models import PBSMMShow
from url_map import url_map

default_data_set = url_map
assets_deleted_data_set = url_map.copy()
assets_deleted_data_set[
    'https://media.services.pbs.org/api/v1/shows/adfb2f9d-f61e-4613-ac58-ab3bde582afb/assets/'
] = 'test_fixtures/nova_shows_adfb2f9d-f61e-4613-ac58-ab3bde582afb_assets_minus_one.json'
assets_deleted_data_set[
    'https://media.services.pbs.org/api/v1/seasons/7f613b59-588b-4ec5-bcb1-a3d595b2579c/assets/'
] = 'test_fixtures/nova_seasons_7f613b59-588b-4ec5-bcb1-a3d595b2579c_assets_minus_one.json'
assets_deleted_data_set[
    'https://media.services.pbs.org/api/v1/specials/a3410528-7f72-47e8-b28d-6861693b9309/assets/'
] = 'test_fixtures/nova_specials_a3410528-7f72-47e8-b28d-6861693b9309_assets_minus_one.json'
assets_deleted_data_set[
    'https://media.services.pbs.org/api/v1/episodes/107268fc-0437-4877-8c3b-d5fdcef32737/assets/'
] = 'test_fixtures/nova_episodes_107268fc-0437-4877-8c3b-d5fdcef32737_assets_minus_one.json'

data_set = default_data_set


def get_api_json(url):
    with open(data_set[url], 'r') as data_file:
        return json.load(data_file)


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

    try:
        response = get_api_json(args[0])
        return MockResponse(response, 200)
    except KeyError:
        return MockResponse(None, 404)


class ShowIngestTestCase(unittest.TestCase):
    @mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
    def setUp(self, mock_get):
        try:
            PBSMMShow.objects.get(slug='nova')
        except ObjectDoesNotExist:
            nova = PBSMMShow()
            nova.slug = 'nova'
            nova.ingest_on_save = True
            nova.ingest_seasons = True
            nova.ingest_specials = True
            nova.ingest_episodes = True
            nova.save()

    @mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
    def reingest(
            self,
            mock_get,
            ingest_seasons=False,
            ingest_specials=False,
            ingest_episodes=False
    ):
        nova = PBSMMShow.objects.get(slug='nova')
        nova.ingest_seasons = ingest_seasons
        nova.ingest_specials = ingest_specials
        nova.ingest_episodes = ingest_episodes
        nova.ingest_on_save = True
        nova.save()

    @mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
    def test_show_ingested(self, mock_get):
        nova = PBSMMShow.objects.get(slug='nova')
        self.assertEqual(nova.object_id, UUID('adfb2f9d-f61e-4613-ac58-ab3bde582afb'))
        self.assertEqual(nova.get_absolute_url(), '/shows/nova/')

    @mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
    def test_show_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest()
        nova_show_asset = Asset.objects.get(
            slug='nova-switching-genes-on-and-off'
        )
        self.assertEqual(
            nova_show_asset.object_id, UUID('bae3b21e-2465-4629-afce-1f192c7a11c9')
        )
        data_set = assets_deleted_data_set
        self.reingest()
        data_set = default_data_set
        with self.assertRaises(Asset.DoesNotExist):
            Asset.objects.get(slug='nova-switching-genes-on-and-off')

    @mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
    def test_season_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest(ingest_seasons=True)
        landslides = Asset.objects.get(slug='predicting-landslides-qh7jt9')
        self.assertEqual(landslides.title, 'Predicting Landslides')
        data_set = assets_deleted_data_set
        self.reingest(ingest_seasons=True)
        with self.assertRaises(Asset.DoesNotExist):
            Asset.objects.get(slug='predicting-landslides-qh7jt9')

    @mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
    def test_special_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest(ingest_specials=True)
        saturn = Asset.objects.get(slug='front-row-seat-saturn-0vf9j2')
        self.assertEqual(saturn.title, 'Front Row Seat to Saturn')
        data_set = assets_deleted_data_set
        self.reingest(ingest_specials=True)
        with self.assertRaises(Asset.DoesNotExist):
            Asset.objects.get(slug='front-row-seat-saturn-0vf9j2')

    @mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
    def test_episode_asset(self, mock_get):
        global data_set
        data_set = default_data_set
        self.reingest(ingest_episodes=True, ingest_seasons=True)
        make_life = Asset.objects.get(slug='can-we-make-life-hquxsp')
        self.assertEqual(make_life.title, 'Can We Make Life? Preview')
        data_set = assets_deleted_data_set
        self.reingest(ingest_episodes=True, ingest_seasons=True)
        with self.assertRaises(Asset.DoesNotExist):
            Asset.objects.get(slug='can-we-make-life-hquxsp')
