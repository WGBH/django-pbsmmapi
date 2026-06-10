from django.conf import settings

try:
    PBSMM_BASE_URL = settings.PBSMM_BASE_URL
except AttributeError:
    PBSMM_BASE_URL = "https://media.services.pbs.org/"
