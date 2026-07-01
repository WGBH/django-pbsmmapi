from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import (
    Cast,
    Coalesce,
)
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    GenericProvisional,
    PBSMMGenericSeason,
)
from pbsmmapi.api.api import PBSMM_SEASON_ENDPOINT
from pbsmmapi.episode.models import Episode
from pbsmmapi.record.models import (
    ContentRecord,
    PBSMMBaseRecordManager,
)


class PBSMMSeasonManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                internal_links=Coalesce(
                    Cast(KT("api_data__data__attributes__links"), models.JSONField()),
                    models.Value([], models.JSONField()),
                ),
                show_content_id=Cast(
                    KT("api_data__data__attributes__show__id"), models.UUIDField()
                ),
            )
        )


class Season(GenericProvisional, PBSMMGenericSeason):
    objects = PBSMMSeasonManager()
    Record = ContentRecord

    ordinal = models.PositiveIntegerField(
        _("Ordinal"),
        null=True,
        blank=True,
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

    mm_content = models.OneToOneField(
        "record.ContentRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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
        out += "\n\t<td>%s</td>" % self.last_updated_display()
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        return mark_safe(out)

    @classmethod
    def realize(cls, data: dict, skip_ingest: bool = False):
        try:
            season = cls.objects.get(
                show_api_id=data["data"]["attributes"]["show"]["id"],
                ordinal=data["data"]["attributes"]["ordinal"],
                provisional=True,
            )
            object_id = data["data"]["id"]
            season.object_id = object_id
            season.provisional = False
            season.save(skip_ingest=skip_ingest)
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

    @property
    def query_param(self):
        return None

    @property
    def endpoint(self):
        return PBSMM_SEASON_ENDPOINT

    def _pre_save_update_fields(self, json_data, content):
        self.title = json_data["data"]["attributes"]["title"]
        self.mm_content = content

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False)
        content_id = kwargs.pop("content_id", None)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            self.pre_save(content_id)
            super().save(*args, **kwargs)
            self.post_save(self.id)

    @classmethod
    @db_task()
    def post_save(cls, season_id):
        """
        If the ingest_episodes flag is set, then also ingest every
        episode for this Season.
        Also, always ingest the Assets associated with this Season.
        """
        season = cls.objects.get(id=season_id)
        links = season.links
        season.process_episodes(links.get("episodes"))
        endpoint = None
        if assets := links.get("assets"):
            endpoint = f"{assets}?platform-slug=partnerplayer"
        season.process_assets(endpoint, season_id=season_id)
        season.stop_ingestion_restart()
        # season.delete_stale_assets(season_id=season_id)

    def process_episodes(self, endpoint):
        if not self.ingest_episodes:
            return

        def set_episode(mm_episode_data: dict, _):
            # If a provisional Episode exists for this ordinal, realize it first
            # so its object_id is set. Otherwise the get_or_create() below would
            # create a duplicate and later changelog realization would raise an
            # IntegrityError on the unique object_id constraint. Promote without
            # ingesting (skip_ingest=True); the save() below runs the single
            # ingest pass.
            # attributes = episode.setdefault("attributes", {})
            # season_ref = {"id": str(self.object_id)}
            # attributes.setdefault("season", season_ref)
            # Episode.realize({"data": episode}, skip_ingest=True)
            try:
                episode = Episode.objects.get(content_id=mm_episode_data["id"])
                episode.save()
            except Episode.DoesNotExist:
                episode = Episode(
                    season_id=self.id,
                    ingest_on_save=True,
                )
                episode.save(content_id=mm_episode_data["id"])

        self.flip_api_pages(endpoint, set_episode)

    def stop_ingestion_restart(self):
        Season.objects.filter(id=self.id).update(
            ingest_episodes=False,
        )

    def __str__(self):
        return f"{self.content_id} | {self.ordinal} | {self.title}"

    class Meta:
        verbose_name = "PBS MM Season"
        verbose_name_plural = "PBS MM Seasons"
        db_table = "pbsmm_season"
        ordering = ["-ordinal"]
