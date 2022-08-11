# -*- coding: utf-8 -*-
from http import HTTPStatus

from django.db import models
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import PBSMMGenericShow
from pbsmmapi.api.api import PBSMM_SHOW_ENDPOINT
from pbsmmapi.asset.models import Asset
from pbsmmapi.season.models import PBSMMSeason
from pbsmmapi.special.models import PBSMMSpecial


class PBSMMShow(PBSMMGenericShow):

    ingest_seasons = models.BooleanField(
        _('Ingest Seasons'),
        default=False,
        help_text='Also ingest all Seasons',
    )
    ingest_specials = models.BooleanField(
        _('Ingest Specials'),
        default=False,
        help_text='Also ingest all Specials',
    )
    ingest_episodes = models.BooleanField(
        _('Ingest Episodes'),
        default=False,
        help_text='Also ingest all Episodes (for each Season)',
    )

    @property
    def object_model_type(self):
        # This handles the correspondence to the "type" field in the PBSMM JSON
        # object
        return 'show'

    class Meta:
        verbose_name = 'PBS MM Show'
        verbose_name_plural = 'PBS MM Shows'
        db_table = 'pbsmm_show'

    def __str__(self):
        if self.title:
            return self.title
        return "ID %d: unknown" % self.id

    def save(self, *args, **kwargs):
        self.pre_save()
        super().save(*args, **kwargs)
        self.post_save(self.id)

    def pre_save(self):
        attrs = self.process(PBSMM_SHOW_ENDPOINT)
        if not attrs:
            return
        self.ga_page = attrs.get('tracking_ga_page')
        self.ga_event = attrs.get('tracking_ga_event')
        self.episode_count = attrs.get('episodes_count')

    @staticmethod
    @db_task()
    def post_save(show_id):
        show = PBSMMShow.objects.get(id=show_id)
        if int(show.last_api_status or 200) != HTTPStatus.OK:
            return  # run only new object or had previous api call success
        show.process_assets(show.json['links'].get('assets'), show_id=show_id)
        show.process_seasons()
        show.process_specials()
        show.delete_stale_assets(show_id=show_id)
        show.stop_ingestion_restart()

    def process_seasons(self):
        if not self.ingest_seasons:
            return

        def set_season(season: dict, _):
            PBSMMSeason.objects.update_or_create(
                defaults=dict(
                    show_id=self.id,
                    ingest_episodes=self.ingest_episodes,
                    show_api_id=self.object_id),
                object_id=season['id'])
        self.flip_api_pages(self.json['links'].get('seasons'), set_season)

    def process_specials(self):
        if not self.ingest_specials:
            return

        def set_special(special: dict, _):
            PBSMMSpecial.objects.update_or_create(
                defaults=dict(
                    show_id=self.id,
                    ingest_on_save=True),
                object_id=special['id'])
        self.flip_api_pages(self.json['links'].get('specials'), set_special)

    def stop_ingestion_restart(self):
        PBSMMShow.objects.filter(id=self.id).update(
            ingest_seasons=False,
            ingest_specials=False,
            ingest_episodes=False)
