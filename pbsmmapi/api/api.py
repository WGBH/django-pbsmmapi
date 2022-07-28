import requests
from http import HTTPStatus
from django.conf import settings


PBSMM_EPISODE_ENDPOINT = 'https://media.services.pbs.org/api/v1/episodes/'
PBSMM_SEASON_ENDPOINT = 'https://media.services.pbs.org/api/v1/seasons/'


def get_PBSMM_record(url: str) -> tuple[int, dict]:
    '''
    This makes the call to the PBS MM API.

    It requires that the PBSMM_API_ID and PBSMM_API_SECRET values be set in the
    project's settings.py file.

    It takes an endpoint URL and returns the status_code at that endpoint and
    the JSON returned.

    No other checking/analysis is done.
    '''
    r = requests.get(url, auth=(settings.PBSMM_API_ID, settings.PBSMM_API_SECRET))
    if r.status_code == HTTPStatus.OK:
        return r.status_code, r.json()
    return r.status_code, dict()
