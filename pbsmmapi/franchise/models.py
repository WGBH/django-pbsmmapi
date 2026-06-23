from http import HTTPStatus

from django.db import models
from django.db.models.fields.json import KT
from django.db.models.functions import Cast
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import (
    PBSMMBaseRecordManager,
    PBSMMGenericFranchise,
)
from pbsmmapi.api.api import PBSMM_FRANCHISE_ENDPOINT
from pbsmmapi.show.models import Show


class PBSMMFranchiseManager(PBSMMBaseRecordManager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(
                nola=KT("api_data__data__attributes__nola"),
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
                internal_links=Cast(
                    KT("api_data__data__attributes__links"), models.JSONField()
                ),
                genre=Cast(KT("api_data__data__attributes__genre"), models.JSONField()),
                platforms=Cast(
                    KT("api_data__data__attributes__platforms"), models.JSONField()
                ),
            )
        )


class Franchise(PBSMMGenericFranchise):
    objects = PBSMMFranchiseManager()

    ingest_shows = models.BooleanField(
        _("Ingest Shows"),
        default=False,
        help_text="Also ingest all Shows",
    )
    ingest_seasons = models.BooleanField(
        _("Ingest Seasons"),
        default=False,
        help_text="Also ingest all Seasons (for each Show)",
    )
    ingest_specials = models.BooleanField(
        _("Ingest Specials"),
        default=False,
        help_text="Also ingest all Show Specials",
    )
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

    def save(self, *args, **kwargs):
        skip_ingest = kwargs.pop("skip_ingest", False)
        if skip_ingest:
            super().save(*args, **kwargs)
        else:
            self.pre_save()
            super().save(*args, **kwargs)
            self.post_save(self.id)

    def pre_save(self):
        attrs = self.process(PBSMM_FRANCHISE_ENDPOINT)
        if not attrs:
            return
        self.ga_page = attrs.get("tracking_ga_page")
        self.ga_event = attrs.get("tracking_ga_event")

    @staticmethod
    @db_task()
    def post_save(franchise_id):
        franchise = Franchise.objects.get(id=franchise_id)
        if int(franchise.last_api_status or 200) != HTTPStatus.OK:
            return  # run only new object or had previous api call success

        franchise.process_assets(
            franchise.json["links"].get("assets"), franchise_id=franchise_id
        )
        franchise.process_shows()
        franchise.delete_stale_assets(franchise_id=franchise_id)

    def process_shows(self):
        if not self.ingest_shows:
            return

        def set_show(show: dict, _):
            # Realize any provisional Show with this title first so its object_id
            # is set; otherwise update_or_create() keyed on object_id would
            # create a duplicate and later changelog realization would raise an
            # IntegrityError on the unique object_id constraint. Promote without
            # ingesting (skip_ingest=True) and let the update_or_create() below
            # run the single ingest pass with the correct ingest flags.
            Show.realize({"data": show}, skip_ingest=True)
            Show.objects.update_or_create(
                defaults=dict(
                    franchise_id=self.id,
                    ingest_seasons=self.ingest_seasons,
                    ingest_episodes=self.ingest_episodes,
                    ingest_specials=self.ingest_specials,
                    franchise_api_id=self.object_id,
                ),
                object_id=show["id"],
            )

        endpoint = None
        if shows := self.json["links"].get("shows"):
            endpoint = f"{shows}?platform-slug=partnerplayer"
        self.flip_api_pages(endpoint, set_show)

    def stop_ingestion_restart(self):
        Franchise.objects.filter(id=self.id).update(
            ingest_shows=False,
            ingest_seasons=False,
            ingest_episodes=False,
            ingest_specials=False,
        )

    def __str__(self):
        if self.title:
            return self.title
        return f"ID {self.id}: unknown"

    class Meta:
        verbose_name = "PBS MM Franchise"
        verbose_name_plural = "PBS MM Franchises"
        db_table = "pbsmm_franchise"
