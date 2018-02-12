import requests

PBSMM_API_ID = 'I5e64vKNUxGb1p0h'
PBSMM_API_SECRET = 'co12wGUvZmauHv7lNGb27nOlkUrbUBgV'

def get_PBSMM_record(url):
    r = requests.get(url, auth=(PBSMM_API_ID, PBSMM_API_SECRET))
    if r.status_code == 200:
        return (r.status_code, r.json())
    else:
        return (r.status_code, None)