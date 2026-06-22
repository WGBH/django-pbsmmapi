from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import Cast
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    GenericProvisional,
    PBSMMBaseRecordManager,
    PBSMMGenericEpisode,
)
from pbsmmapi.api.api import PBSMM_EPISODE_ENDPOINT


class PBSMMEpisodeManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                nola=KT("api_data__data__attributes__nola"),
                language=KT("api_data__data__attributes__language"),
                internal_links=Cast(
                    KT("api_data__data__attributes__links"), models.JSONField()
                ),
                premiered_on=Cast(
                    KT("api_data__data__attributes__premiered_on"),
                    models.DateField(),
                ),
                encored_on=Cast(
                    KT("api_data__data__attributes__encored_on"), models.DateTimeField()
                ),
                season_content_id=Cast(
                    KT("api_data__data__attributes__season__id"), models.UUIDField()
                ),
            )
        )


class Episode(GenericProvisional, PBSMMGenericEpisode):
    """
    These are the fields that are unique to Episode records.
    """

    objects = PBSMMEpisodeManager()

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
    mm_content = models.OneToOneField(
        "record.ContentRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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
