from django.conf import settings
from huey import crontab
from huey.contrib.djhuey import db_periodic_task

from pbsmmapi.show.models import Show


@db_periodic_task(crontab(minute="0"))
def scrape_media_manager_shows():
    show_slugs = getattr(settings, "PBSMM_SHOW_SLUGS", [])
    for slug in show_slugs:
        try:
            show = Show.objects.get(slug=slug)
            if show.seasons.exists():  # already ingested
                continue
        except Show.DoesNotExist:
            show = Show(slug=slug)

        show.ingest_on_save = True
        show.ingest_seasons = True
        show.ingest_specials = True
        show.ingest_episodes = True
        show.save()
