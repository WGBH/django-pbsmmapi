# -*- coding: utf-8 -*-
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task

from pbsmmapi.abstract.models import PBSMMGenericSeason
from pbsmmapi.api.api import PBSMM_SEASON_ENDPOINT
from pbsmmapi.asset.models import Asset
from pbsmmapi.episode.models import PBSMMEpisode


class PBSMMSeason(PBSMMGenericSeason):
    '''
    These are the fields that are unique to PBSMMSeason
    '''
    ordinal = models.PositiveIntegerField(_('Ordinal'), null=True, blank=True)

    # This is the parental Show
    show_api_id = models.UUIDField(
        _('Show Object ID'),
        null=True,
        blank=True  # does this work?
    )
    show = models.ForeignKey(
        'show.PBSMMShow',
        related_name='seasons',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # This triggers cascading ingestion of child Episodes - set from the admin
    # before a save()
    ingest_episodes = models.BooleanField(
        _('Ingest Episodes'),
        default=False,
        help_text='Also ingest all Episodes (for each Season)'
    )

    def create_table_line(self):
        this_title = "Season %d: %s" % (self.ordinal, self.title)
        out = "<tr style=\"background-color: #ddd;\">"
        out += "<td colspan=\"3\"><a href=\"/admin/season/pbsmmseason/%d/change/\"><b>%s</b></a></td>" % (
            self.id, this_title
        )
        out += "<td><a href=\"%s\" target=\"_new\">API</a></td>" % self.api_endpoint
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        return mark_safe(out)

    @property
    def object_model_type(self):
        '''
        This return the object type.
        '''
        # This handles the correspondence to the "type" field in the PBSMM JSON
        # object
        return 'season'

    @property
    def printable_title(self):
        '''
        This creates a human friendly title out of the Season metadata
        if an explicit title is not set from the Show title and Episode ordinal.
        '''
        if self.show:
            return f'{self.show.title} Season {self.ordinal}'
        return 'Season {self.ordinal}'

    def __str__(self):
        return f'{self.object_id} | {self.ordinal} | {self.title}'

    class Meta:
        verbose_name = 'PBS MM Season'
        verbose_name_plural = 'PBS MM Seasons'
        db_table = 'pbsmm_season'
        ordering = ['-ordinal']

    def save(self, *args, **kwargs):
        self.pre_save()
        super().save(args, kwargs)
        self.post_save(self.id)

    def pre_save(self):
        self.process(PBSMM_SEASON_ENDPOINT)

    @db_task()
    def post_save(self, season_id):
        '''
        If the ingest_episodes flag is set, then also ingest every
        episode for this Season.
        Also, always ingest the Assets associated with this Season.
        '''
        season = PBSMMSeason.objects.get(id=season_id)
        links = season.json.get('links', dict())
        if season.ingest_episodes:
            self.process_episodes(links.get('episodes'))
        self.process_assets(links.get('assets'), season_id=season_id)
        PBSMMSeason.objects.filter(id=season_id).update(ingest_episodes=False)
        self.delete_stale_assets(season_id=season_id)
        # !!! this ^ needs to be checked !!!

    @db_task()
    def process_episodes(self, endpoint):
        def set_episode(episode: dict, _):
            obj, created = PBSMMEpisode.objects.get_or_create(
                object_id=episode['id'])
            obj.save()
        self.flip_api_pages(endpoint, set_episode)
