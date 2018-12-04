# -*- coding: utf-8 -*-
import datetime
from uuid import UUID
from django.test import TestCase

from pbsmmapi.episode.models import PBSMMEpisode


class EpisodeTestCase(TestCase):
    def setUp(self):
        PBSMMEpisode.objects.create(
            date_created=datetime.datetime(2018, 10, 5, 3, 23, 46, 225183),
            date_last_api_update=datetime.datetime(
                2018, 12, 3, 11, 1, 9, 240615),
            ingest_on_save=False,
            last_api_status=200,
            json={
                'data': {
                    'type': 'episode',
                    'id': 'cea8cc54-0a16-4cc1-88e6-cdd65728aab2',
                    'attributes': {'ordinal': 106,
                                   'segment': '',
                                   'title': "NOVA Wonders What's the Universe Made Of?",
                                   'title_sortable': "NOVA Wonders What's the Universe Made Of?",
                                   'slug': 'nova-wonders-whats-universe-made-xszshk',
                                   'tms_id': '',
                                   'description_short': 'Peer into the deep unknowns of the universe to explore its mysteries.',
                                   'description_long': 'The universe is hiding something. In fact, it is hiding a lot. Everything we experience on Earth, the stars and galaxies we see in the cosmos—all the “normal” matter and energy that we understand—make up only 5% of the known universe. Find out how scientists are discovering new secrets about the history of the universe, and why they’re predicting a shocking future.',
                                   'premiered_on': '2018-04-04',
                                   'encored_on': '2018-04-04',
                                   'nola': '',
                                   'language': 'en',
                                   'updated_at': '2018-11-01T01:23:23.381193Z',
                                   'season': {'type': 'season',
                                              'links': {'self': 'https://media.services.pbs.org/api/v1/seasons/7f613b59-588b-4ec5-bcb1-a3d595b2579c/'},
                                              'id': '7f613b59-588b-4ec5-bcb1-a3d595b2579c',
                                              'attributes': {'ordinal': 45,
                                                             'title': '',
                                                             'title_sortable': '',
                                                             'updated_at': '2018-11-28T21:42:48.201870Z'}},
                                   'show': {'type': 'show',
                                            'links': {'self': 'https://media.services.pbs.org/api/v1/shows/adfb2f9d-f61e-4613-ac58-ab3bde582afb/'},
                                            'id': 'adfb2f9d-f61e-4613-ac58-ab3bde582afb',
                                            'attributes': {'title': 'NOVA',
                                                           'title_sortable': 'NOVA',
                                                           'slug': 'nova',
                                                           'display_episode_number': True,
                                                           'updated_at': '2018-11-29T18:59:09.163954Z'}},
                                   'links': [{'value': 'https://shop.pbs.org/product/NV61711?utm_source=PBS&utm_medium=Link&utm_content=nova_wonders_S1_covebuyit&utm_campaign=cove_buyit',
                                              'profile': 'buy-dvd',
                                              'updated_at': '2018-04-18T16:45:53.318679Z'},
                                             {'value': 'https://geo.itunes.apple.com/us/tv-season/nova-wonders/id1359820361?4&at=11l3Sf&ct=NOVAWondersMM',
                                              'profile': 'itunes',
                                              'updated_at': '2018-08-01T17:02:05.452820Z'},
                                             {'value': 'https://www.amazon.com/gp/product/B07CTNRS93/ref=as_li_tl?ie=UTF8&tag=p05a2-20&camp=1789&creative=9325&linkCode=as2&creativeASIN=B07CTNRS93&linkId=4b9487270e39e1af4e95b18b3af02846',
                                              'profile': 'amazon',
                                              'updated_at': '2018-08-01T17:02:05.490584Z'}]}
                },
                'links': {'self': 'https://media.services.pbs.org/api/v1/episodes/cea8cc54-0a16-4cc1-88e6-cdd65728aab2/',
                          'assets': 'https://media.services.pbs.org/api/v1/episodes/cea8cc54-0a16-4cc1-88e6-cdd65728aab2/assets/',
                          'collections': 'https://media.services.pbs.org/api/v1/episodes/cea8cc54-0a16-4cc1-88e6-cdd65728aab2/collections/'},
                'jsonapi': {'version': '1.0'},
                'meta': {'type': 'resource'}
            },
            publish_status=0,
            live_as_of=None,
            object_id=UUID('cea8cc54-0a16-4cc1-88e6-cdd65728aab2'),
            api_endpoint='https://media.services.pbs.org/api/v1/episodes/cea8cc54-0a16-4cc1-88e6-cdd65728aab2/',
            title="NOVA Wonders What's the Universe Made Of?",
            title_sortable="NOVA Wonders What's the Universe Made Of?",
            slug='nova-wonders-whats-universe-made-xszshk',
            description_long='The universe is hiding something. In fact, it is hiding a lot. Everything we experience on Earth, the stars and galaxies we see in the cosmos—all the “normal” matter and energy that we understand—make up only 5% of the known universe. Find out how scientists are discovering new secrets about the history of the universe, and why they’re predicting a shocking future.',
            description_short='Peer into the deep unknowns of the universe to explore its mysteries.',
            updated_at=datetime.datetime(2018, 11, 1, 1, 23, 23, 381193),
            premiered_on=datetime.datetime(2018, 4, 4, 0, 0),
            nola='',
            images=None,
            canonical_image_type_override=None,
            funder_message=None,
            links='[{"value": "https://shop.pbs.org/product/NV61711?utm_source=PBS&utm_medium=Link&utm_content=nova_wonders_S1_covebuyit&utm_campaign=cove_buyit", "profile": "buy-dvd", "updated_at": "2018-04-18T16:45:53.318679Z"}, {"value": "https://geo.itunes.apple.com/us/tv-season/nova-wonders/id1359820361?4&at=11l3Sf&ct=NOVAWondersMM", "profile": "itunes", "updated_at": "2018-08-01T17:02:05.452820Z"}, {"value": "https://www.amazon.com/gp/product/B07CTNRS93/ref=as_li_tl?ie=UTF8&tag=p05a2-20&camp=1789&creative=9325&linkCode=as2&creativeASIN=B07CTNRS93&linkId=4b9487270e39e1af4e95b18b3af02846", "profile": "amazon", "updated_at": "2018-08-01T17:02:05.490584Z"}]',
            language='en',
            encored_on=datetime.datetime(2018, 4, 4, 0, 0),
            ordinal=106,
            segment='',
            season_id=1
        )

    def test_slug(self):
        episode = PBSMMEpisode.objects.get(
            title="NOVA Wonders What's the Universe Made Of?"
        )
        self.assertEqual(
            episode.slug,
            'nova-wonders-whats-universe-made-xszshk')
