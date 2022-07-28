# -*- coding: utf-8 -*-
from http import HTTPStatus

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from huey.contrib.djhuey import db_task
from pbsmmapi.abstract.helpers import time_zone_aware_now, \
    fix_non_aware_datetime
from pbsmmapi.abstract.models import PBSMMGenericEpisode
from pbsmmapi.api.api import get_PBSMM_record, PBSMM_EPISODE_ENDPOINT
from pbsmmapi.api.helpers import check_pagination
from pbsmmapi.asset.models import Asset


class PBSMMEpisode(PBSMMGenericEpisode):
    '''
    These are the fields that are unique to Episode records.
    '''

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.scraped_object_ids = list()

    encored_on = models.DateTimeField(
        _('Encored On'),
        blank=True,
        null=True,
    )
    ordinal = models.PositiveIntegerField(
        _('Ordinal'),
        blank=True,
        null=True,
    )
    segment = models.CharField(
        _('Segment'),
        max_length=200,
        blank=True,
        null=True,
    )

    # THIS IS THE PARENTAL SEASON
    season = models.ForeignKey(
        'season.PBSMMSeason',
        related_name='episodes',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    season_api_id = models.UUIDField(
        _('Season Object ID'),
        null=True,
        blank=True,  # does this work?
    )

    @property
    def object_model_type(self):
        '''
        This just returns object "type"
        '''
        return 'episode'

    @property
    def full_episode_code(self):
        '''
        This just formats the Episode as:
            show-XXYY where XX is the season and YY is the ordinal, e.g.,:  roadshow-2305
            for Roadshow, Season 23, Episode 5.

            Useful in lists of episodes that cross Seasons/Shows.
        '''
        if self.season and self.season.show and self.season.ordinal:
            return f'{self.season.show.slug}-{self.season.ordinal:02d}-{self.ordinal:02d}'
        return f'{self.pk}: (episode {self.ordinal})'

    def short_episode_code(self):
        '''
        This is just the Episode "code" without the Show slug, e.g.,  0523 for
        the 23rd episode of Season 5
        '''
        return f'{self.season.ordinal:02d}{self.ordinal:02d}'

    short_episode_code.short_description = 'Ep #'

    @property
    def nola_code(self):
        if self.nola is None or self.nola == '':
            return None
        if self.season.show.nola is None or self.season.show.nola == '':
            return None
        return f'{self.season.show.nola}{self.nola}'

    def create_table_line(self):
        '''
        This just formats a line in a Table of Episodes.
        Used on a Season's admin page and a Show's admin page.
        '''
        out = "<tr>"
        out += "\t<td></td>"
        out += "\n\t<td>%02d%02d:</td>" % (self.season.ordinal, self.ordinal)
        out += "\n\t<td><a href=\"/admin/episode/pbsmmepisode/%d/change/\"><b>%s</b></td>" % (
            self.id, self.title
        )
        out += "\n\t<td><a href=\"%s\" target=\"_new\">API</a></td>" % self.api_endpoint
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        return mark_safe(out)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'PBS MM Episode'
        verbose_name_plural = 'PBS MM Episodes'
        db_table = 'pbsmm_episode'

    def save(self, *args, **kwargs):
        self.pre_save()
        super().save(*args, **kwargs)
        self.post_save(self.id)

    def pre_save(self):
        # object_id = str(self.object_id or "").strip()
        # if not self.ingest_on_save or self.pk or not object_id:
        #     return  # we need processing only for new objects
        # status, json = get_PBSMM_record(f"{PBSMM_EPISODE_ENDPOINT}{object_id}/")
        # self.object_id = object_id
        # self.last_api_status = status
        # self.date_last_api_update = time_zone_aware_now()
        # if status != HTTPStatus.OK:
        #     return
        # attrs = json.get('attributes', json['data'].get('attributes'))
        # fields = (f.name for f in PBSMMEpisode._meta.get_fields())
        # for field in (f for f in fields if f != 'id'):
        #     setattr(self, field, attrs.get(field))
        # self.updated_at = fix_non_aware_datetime(attrs.get('updated_at'))
        # self.api_endpoint = json['links'].get('self')
        # self.links = attrs.get('links')
        # self.season_api_id = attrs.get('season', dict()).get('id', None)
        # self.json = json
        # self.ingest_on_save = False
        self.self_process(PBSMM_EPISODE_ENDPOINT)

    @staticmethod
    @db_task()
    def post_save(episode_id):
        episode = PBSMMEpisode.object_id.get(id=episode_id)
        episode.process_assets(episode.json['links'].get('assets'))
        Asset.objects.filter(episode=episode).exclude(
            object_id__in=episode.scraped_object_ids).delete()

    def process_assets(self, endpoint):
        status, json = get_PBSMM_record(endpoint)
        for asset in json.get('data', list()):
            self.scraped_object_ids.append(asset['id'])
            Asset.set(asset, last_api_status=status, episode_id=self.id)
        keep_going, endpoint = check_pagination(json)
        if keep_going:
            self.process_assets(endpoint)


# PBS MediaManager API interface

# The interface/access is done with a 'pre_save' receiver based on the value of
# 'ingest_on_save' That way, one can force a reingestion from the Admin OR one
# can do it from a management script by simply getting the record, setting
# ingest_on_save on the record, and calling save().


# @receiver(models.signals.pre_save, sender=PBSMMEpisode)
# def scrape_PBSMMAPI(sender, instance, **kwargs):
#     '''
#     This calls the PBS MM API for an Episode and then either saves or creates it.
#     '''
#     if instance.__class__ is not PBSMMEpisode:
#         return
#
#     # If this is a new record, then someone has started it in the Admin using
#     # EITHER a legacy COVE ID OR a PBSMM UUID. Depending on which, the
#     # retrieval endpoint is slightly different, so this sets the appropriate
#     # URL to access.
#     if instance.pk and instance.object_id and str(instance.object_id).strip():
#         # Object is being edited
#         op = 'edit'
#
#     else:  # object is being added
#         op = 'create'
#         if not instance.object_id:
#             return  # do nothing - can't get an ID to look up!
#
#     if op == 'create' or instance.ingest_on_save:
#         url = "{}{}/".format(PBSMM_EPISODE_ENDPOINT, instance.object_id)
#
#         # OK - get the record from the API
#         (status, json) = get_PBSMM_record(url)
#
#         instance.last_api_status = status
#         # Update this record's time stamp (the API has its own)
#         instance.date_last_api_update = time_zone_aware_now()
#
#         # If we didn't get a record, abort (there's no sense crying over
#         # spilled bits)
#         if status != 200:
#             return
#
#         # Process the record (code is in ingest.py)
#         instance = process_episode_record(json, instance)
#
#         # continue saving, but turn off the ingest_on_save flag
#         instance.ingest_on_save = False  # otherwise we could end up in an infinite loop!
#
#     # We're done here - continue with the save() operation
#     return instance
