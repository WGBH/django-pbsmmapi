from http import HTTPStatus

from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import Cast
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    GenericProvisional,
    PBSMMBaseRecordManager,
    PBSMMGenericShow,
)
from pbsmmapi.api.api import PBSMM_SHOW_ENDPOINT
from pbsmmapi.record.models import ContentRecord
from pbsmmapi.season.models import Season
from pbsmmapi.special.models import Special


class PBSMMShowManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                nola=KT("api_data__data__attributes__nola"),
                tms_id=KT("api_data__data__attributes__tms_id"),
                premiered_on=Cast(
                    KT("api_data__data__attributes__premiered_on"),
                    models.DateField(),
                ),
                funder_message=KT("api_data__data__attributes__funder_message"),
                tracking_ga_page=KT("api_data__data__attributes__tracking_ga_page"),
                tracking_ga_event=KT("api_data__data__attributes__tracking_ga_event"),
                is_excluded_from_dfp=Cast(
                    KT("api_data__data__attributes__is_excluded_from_dfp"),
                    models.BooleanField(),
                ),
                can_embed_player=Cast(
                    KT("api_data__data__attributes__can_embed_player"),
                    models.BooleanField(),
                ),
                language=KT("api_data__data__attributes__language"),
                genre=Cast(KT("api_data__data__attributes__genre"), models.JSONField()),
                internal_links=Cast(
                    KT("api_data__data__attributes__links"), models.JSONField()
                ),
                audience=Cast(
                    KT("api_data__data__attributes__audience"), models.JSONField()
                ),
                sort_episodes_descending=Cast(
                    KT("api_data__data__attributes__sort_episodes_descending"),
                    models.BooleanField(),
                ),
                display_episode_number=Cast(
                    KT("api_data__data__attributes__display_episode_number"),
                    models.BooleanField(),
                ),
                platforms=Cast(
                    KT("api_data__data__attributes__platforms"), models.JSONField()
                ),
                franchise_content_id=Cast(
                    KT("api_data__data__attributes__franchise__id"), models.UUIDField()
                ),
                episode_count=Cast(
                    KT("api_data__data__attributes__episodes_count"),
                    models.IntegerField(),
                ),
            )
        )


class Show(GenericProvisional, PBSMMGenericShow):
    objects = PBSMMShowManager()

    ingest_seasons = models.BooleanField(
        _("Ingest Seasons"),
        default=False,
        help_text="Also ingest all Seasons",
    )
    ingest_specials = models.BooleanField(
        _("Ingest Specials"),
        default=False,
        help_text="Also ingest all Specials",
    )
    ingest_episodes = models.BooleanField(
        _("Ingest Episodes"),
        default=False,
        help_text="Also ingest all Episodes (for each Season)",
    )

    # This is the parental Franchise
    franchise_api_id = models.UUIDField(
        _("Franchise Object ID"),
        null=True,
        blank=True,
    )
    franchise = models.ForeignKey(
        "franchise.Franchise",
        related_name="shows",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    ordinal_season = models.BooleanField(
        _("Ordinal Season"),
        default=True,
        help_text="Use incrementing integer or current year when creating a Season",
    )
    mm_content = models.OneToOneField(
        "record.ContentRecord",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    @classmethod
    def realize(cls, data: dict, skip_ingest: bool = False):
        try:
            show = cls.objects.get(
                title=data["data"]["attributes"]["title"],
                provisional=True,
            )
            object_id = data["data"]["id"]
            show.object_id = object_id
            show.provisional = False
            show.save(skip_ingest=skip_ingest)
            Season.objects.filter(
                provisional=True,
                show=show,
                show_api_id__isnull=True,
            ).update(show_api_id=object_id)
            Special.objects.filter(
                provisional=True,
                show=show,
                show_api_id__isnull=True,
            ).update(show_api_id=object_id)
            return show
        except cls.DoesNotExist:
            return None

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False)
        content_id = kwargs.pop("content_id", None)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            status = self.pre_save(content_id)
            super().save(*args, **kwargs)
            self.post_save(self.id, status)

    def pre_save(self, content_id=None):
        status, json_data = self.process(
            PBSMM_SHOW_ENDPOINT, "?platform-slug=partnerplayer", content_id=content_id
        )
        if status != HTTPStatus.OK:
            if self.mm_content is not None:
                self.mm_content.last_api_status = status
                self.mm_content.save()
            return status

        content_id = json_data["data"]["id"]
        content = ContentRecord.update_or_create(
            content_id=content_id,
            last_api_status=status,
            api_data=json_data,
        )
        if self.mm_content is None:
            self.title = json_data["data"]["attributes"]["title"]
            self.slug = json_data["data"]["attributes"]["slug"]
            self.mm_content = content
        return status

    @staticmethod
    @db_task()
    def post_save(show_id, status):
        show = Show.objects.get(id=show_id)
        if status != HTTPStatus.OK:
            return  # run only new object or had previous api call success
        endpoint = None
        if assets := show.links.get("assets"):
            endpoint = f"{assets}?platform-slug=partnerplayer"
        show.process_assets(endpoint, show_id=show_id)
        show.process_seasons()
        show.process_specials()
        # show.delete_stale_assets(show_id=show_id)
        show.stop_ingestion_restart()

    def process_seasons(self):
        if not self.ingest_seasons:
            return

        def set_season(mm_season_data: dict, _):
            # Realize any provisional Season for this ordinal first so its
            # object_id is set; otherwise update_or_create() keyed on object_id
            # would create a duplicate and later changelog realization would
            # raise an IntegrityError on the unique object_id constraint.
            # Promote without ingesting (skip_ingest=True) and let the
            # update_or_create() below run the single ingest pass with the
            # correct ingest flags.
            # attributes = season.setdefault("attributes", {})
            # show_ref = {"id": str(self.object_id)}
            # attributes.setdefault("show", show_ref)
            # Season.realize({"data": season}, skip_ingest=True)
            try:
                season = Season.objects.get(content_id=mm_season_data["id"])
                season.save()
            except Season.DoesNotExist:
                season = Season(
                    show_id=self.id,
                    ingest_on_save=True,
                    ingest_episodes=self.ingest_episodes,
                )
                season.save(content_id=mm_season_data["id"])

        self.flip_api_pages(self.links.get("seasons"), set_season)

    def process_specials(self):
        if not self.ingest_specials:
            return

        def set_special(mm_special_data: dict, _):
            # Realize any provisional Special with this title first so its
            # object_id is set; otherwise update_or_create() keyed on object_id
            # would create a duplicate and later changelog realization would
            # raise an IntegrityError on the unique object_id constraint.
            # Promote without ingesting (skip_ingest=True) and let the
            # update_or_create() below run the single ingest pass.
            # attributes = special.setdefault("attributes", {})
            # show_ref = {"id": str(self.content_id)}
            # attributes.setdefault("show", show_ref)
            # Special.realize({"data": special}, skip_ingest=True)
            try:
                special = Special.objects.get(content_id=mm_special_data["id"])
                special.save()
            except Special.DoesNotExist:
                special = Special(
                    show_id=self.id,
                    ingest_on_save=True,
                )
                special.save(content_id=mm_special_data["id"])

        self.flip_api_pages(
            f"{self.links.get('specials')}?platform-slug=partnerplayer",
            set_special,
        )

    def stop_ingestion_restart(self):
        Show.objects.filter(id=self.id).update(
            ingest_seasons=False,
            ingest_specials=False,
            ingest_episodes=False,
        )

    def create_table_line(self):
        this_title = "Show: %s" % self.title
        out = '<tr style="background-color: #uuu;">'
        out += (
            '<td colspan="3"><a'
            ' href="/admin/show/show/%d/change/"><b>%s</b></a></td>'
            % (self.id, this_title)
        )
        out += '<td><a href="%s" target="_new">API</a></td>' % self.api_endpoint
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.last_updated_display()
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        return mark_safe(out)

    def __str__(self):
        if self.title:
            return self.title
        return "ID %d: unknown" % self.id

    class Meta:
        verbose_name = "PBS MM Show"
        verbose_name_plural = "PBS MM Shows"
        db_table = "pbsmm_show"
