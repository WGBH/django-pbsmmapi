from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from pbsmmapi.franchise.models import Franchise


@db_periodic_task(crontab(minute="0"))
def scrape_media_manager_franchises():
    franchise_slugs = getattr(settings, "PBSMM_FRANCHISE_SLUGS", [])
    for slug in franchise_slugs:
        try:
            franchise = Franchise.objects.get(slug=slug)
            if franchise.shows.exists():  # already ingested
                continue
        except Franchise.DoesNotExist:
            franchise = Franchise(slug=slug)

        franchise.ingest_on_save = True
        franchise.ingest_shows = True
        franchise.ingest_seasons = True
        franchise.ingest_specials = True
        franchise.ingest_episodes = True
        franchise.save()
