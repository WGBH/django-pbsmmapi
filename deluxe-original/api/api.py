import requests
from django.conf import settings

def get_PBSMM_record(url):
    r = requests.get(url, auth=(settings.PBSMM_API_ID, settings.PBSMM_API_SECRET))
    if r.status_code == 200:
        return (r.status_code, r.json())
    else:
        return (r.status_code, None)
        