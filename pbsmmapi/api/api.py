import requests
from django.conf import settings

"""
This makes the call to the PBS MM API.

It requires that the PBSMM_API_ID and PBSMM_API_SECRET values be set in the project's settings.py file.

It takes an endpoint URL and returns the status_code at that endpoint and the JSON returned.

No other checking/analysis is done.
"""


def get_PBSMM_record(url):
    r = requests.get(
        url,
        auth=(
            settings.PBSMM_API_ID,
            settings.PBSMM_API_SECRET))
    if r.status_code == 200:
        return (r.status_code, r.json())
    else:
        return (r.status_code, None)
