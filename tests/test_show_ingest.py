import json
import unittest
from uuid import UUID


try:
    from unittest import mock
except ImportError:
    import mock

from pbsmmapi.show.models import PBSMMShow

with open('test_fixtures/nova_show.json', 'r') as show_file:
    nova_show_data = json.load(show_file)


def get_api_json(url):
    api_map = {
        'https://media.services.pbs.org/api/v1/shows/nova/': 'test_fixtures/nova_show.json',
        'https://media.services.pbs.org/api/v1/shows/adfb2f9d-f61e-4613-ac58-ab3bde582afb/assets/': 'test_fixtures/nova_show_assets.json',
        'https://media.services.pbs.org/api/v1/shows/adfb2f9d-f61e-4613-ac58-ab3bde582afb/assets/?page=2': 'test_fixtures/nova_show_assets_page_2.json',
        'https://media.services.pbs.org/api/v1/shows/adfb2f9d-f61e-4613-ac58-ab3bde582afb/assets/?page=3': 'test_fixtures/nova_show_assets_page_3.json',
    }
    with open(api_map[url], 'r') as data_file:
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


@mock.patch('pbsmmapi.api.api.requests.get', side_effect=mocked_requests_get)
class ShowIngestTestCase(unittest.TestCase):
    def setUp(self):
        new_show = PBSMMShow()
        new_show.slug = 'nova'
        new_show.ingest_on_save = True
        new_show.save()

    def test_get_show(self, mock_get):
        new_show = PBSMMShow.objects.get(slug='nova')
        self.assertEqual(new_show.slug, 'nova')
        self.assertEqual(new_show.object_id, UUID(
            'adfb2f9d-f61e-4613-ac58-ab3bde582afb'))
