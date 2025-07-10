from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    GenericProvisional,
    PBSMMGenericEpisode,
)
from pbsmmapi.api.api import PBSMM_EPISODE_ENDPOINT


class Episode(GenericProvisional, PBSMMGenericEpisode):
    """
    These are the fields that are unique to Episode records.
    """

    encored_on = models.DateTimeField(
        _("Encored On"),
        blank=True,
        null=True,
    )
    ordinal = models.PositiveIntegerField(
        _("Ordinal"),
        blank=True,
        null=True,
    )
    # THIS IS THE PARENTAL SEASON
    season = models.ForeignKey(
        "season.Season",
        related_name="episodes",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    season_api_id = models.UUIDField(
        _("Season Object ID"),
        null=True,
        blank=True,  # does this work?
    )

    @classmethod
    def realize(cls, data: dict):
        try:
            episode = cls.objects.get(
                season_api_id=data["data"]["attributes"]["season"]["id"],
                ordinal=data["data"]["attributes"]["ordinal"],
                provisional=True,
            )
            episode.object_id = data["data"]["id"]
            episode.provisional = False
            episode.save()
        except cls.DoesNotExist:
            return

    @property
    def segment(self):
        """
        Return individual segments of a single episode.
        """
        try:
            return self.json.get("data").get("attributes").get("segment")
        except AttributeError:
            return None

    @property
    def full_episode_code(self):
        """
        This just formats the Episode as:
            show-XXYY where XX is the season and YY is the ordinal,
            e.g.,: roadshow-2305
            for Roadshow, Season 23, Episode 5.

            Useful in lists of episodes that cross Seasons/Shows.
        """
        if self.season and self.season.show and self.season.ordinal:
            return (
                f"{self.season.show.slug}-{self.season.ordinal:02d}-{self.ordinal:02d}"
            )
        return f"{self.pk}: (episode {self.ordinal})"

    def short_episode_code(self):
        """
        This is just the Episode "code" without the Show slug, e.g.,  0523 for
        the 23rd episode of Season 5
        """
        return f"{self.season.ordinal:02d}{self.ordinal:02d}"

    short_episode_code.short_description = "Ep #"

    @property
    def nola_code(self):
        if self.nola is None or self.nola == "":
            return None
        if self.season.show.nola is None or self.season.show.nola == "":
            return None
        return f"{self.season.show.nola}{self.nola}"

    def create_table_line(self):
        """
        This just formats a line in a Table of Episodes.
        Used on a Season's admin page and a Show's admin page.
        """
        out = "<tr>"
        out += "\t<td></td>"
        out += "\n\t<td>%02d%02d:</td>" % (self.season.ordinal, self.ordinal)
        out += (
            '\n\t<td><a href="/admin/episode/pbsmmepisode/%d/change/"><b>%s</b></td>'
            % (self.id, self.title)
        )
        out += '\n\t<td><a href="%s" target="_new">API</a></td>' % self.api_endpoint
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        return mark_safe(out)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "PBS MM Episode"
        verbose_name_plural = "PBS MM Episodes"
        db_table = "pbsmm_episode"

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            self.pre_save()
            super().save(*args, **kwargs)
            self.post_save(self.id)

    def pre_save(self):
        self.process(PBSMM_EPISODE_ENDPOINT)

    @staticmethod
    @db_task()
    def post_save(episode_id):
        episode = Episode.objects.get(id=episode_id)
        endpoint = None
        if assets := episode.json["links"].get("assets"):
            endpoint = f"{assets}?platform-slug=partnerplayer"
        episode.process_assets(
            endpoint,
            episode_id=episode_id,
        )
        episode.delete_stale_assets(episode_id=episode_id)
