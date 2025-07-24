from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    GenericProvisional,
    PBSMMGenericSeason,
)
from pbsmmapi.api.api import PBSMM_SEASON_ENDPOINT
from pbsmmapi.episode.models import Episode


class Season(GenericProvisional, PBSMMGenericSeason):
    ordinal = models.PositiveIntegerField(
        _("Ordinal"),
        null=True,
        blank=True,
    )

    # This is the parental Show
    show_api_id = models.UUIDField(
        _("Show Object ID"),
        null=True,
        blank=True,  # does this work?
    )
    show = models.ForeignKey(
        "show.Show",
        related_name="seasons",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # This triggers cascading ingestion of child Episodes - set from the admin
    # before a save()
    ingest_episodes = models.BooleanField(
        _("Ingest Episodes"),
        default=False,
        help_text="Also ingest all Episodes (for each Season)",
    )

    def create_table_line(self):
        this_title = "Season %d: %s" % (self.ordinal, self.title)
        out = '<tr style="background-color: #ddd;">'
        out += (
            '<td colspan="3"><a'
            ' href="/admin/season/pbsmmseason/%d/change/"><b>%s</b></a></td>'
            % (self.id, this_title)
        )
        out += '<td><a href="%s" target="_new">API</a></td>' % self.api_endpoint
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        return mark_safe(out)

    @classmethod
    def realize(cls, data: dict):
        try:
            season = cls.objects.get(
                show_api_id=data["data"]["attributes"]["show"]["id"],
                ordinal=data["data"]["attributes"]["ordinal"],
                provisional=True,
            )
            object_id = data["data"]["id"]
            season.object_id = object_id
            season.provisional = False
            season.save()
            Episode.objects.filter(
                provisional=True,
                season=season,
                season_api_id__isnull=True,
            ).update(season_api_id=object_id)
            return season
        except cls.DoesNotExist:
            return

    @property
    def printable_title(self):
        """
        This creates a human friendly title out of the Season metadata
        if an explicit title is not set from the Show title and Episode ordinal.
        """
        if self.show:
            return f"{self.show.title} Season {self.ordinal}"
        return f"Season {self.ordinal}"

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            self.pre_save()
            super().save(*args, **kwargs)
            self.post_save(self.id)

    def pre_save(self):
        attrs = self.process(PBSMM_SEASON_ENDPOINT)
        if not attrs:
            return
        self.ga_page = attrs.get("tracking_ga_page")
        self.ga_event = attrs.get("tracking_ga_event")
        # The canonical image used for this is
        # the one that has 'mezzanine' in it
        if self.images is None:  # try latest_asset_images
            self.images = attrs.get("latest_asset_images")

    @staticmethod
    @db_task()
    def post_save(season_id):
        """
        If the ingest_episodes flag is set, then also ingest every
        episode for this Season.
        Also, always ingest the Assets associated with this Season.
        """
        season = Season.objects.get(id=season_id)
        links = season.json.get("links", dict())
        season.process_episodes(links.get("episodes"))
        endpoint = None
        if assets := links.get("assets"):
            endpoint = f"{assets}?platform-slug=partnerplayer"
        season.process_assets(endpoint, season_id=season_id)
        season.stop_ingestion_restart()
        season.delete_stale_assets(season_id=season_id)

    def process_episodes(self, endpoint):
        if not self.ingest_episodes:
            return

        def set_episode(episode: dict, _):
            obj, created = Episode.objects.get_or_create(
                object_id=episode["id"],
            )
            obj.season_id = self.id
            obj.season_api_id = self.object_id
            obj.save()

        self.flip_api_pages(endpoint, set_episode)

    def stop_ingestion_restart(self):
        Season.objects.filter(id=self.id).update(
            ingest_episodes=False,
        )

    def __str__(self):
        return f"{self.object_id} | {self.ordinal} | {self.title}"

    class Meta:
        verbose_name = "PBS MM Season"
        verbose_name_plural = "PBS MM Seasons"
        db_table = "pbsmm_season"
        ordering = ["-ordinal"]
