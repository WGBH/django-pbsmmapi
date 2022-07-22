# -*- coding: utf-8 -*-
from uuid import UUID

from django.db import models
from django.dispatch import receiver
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from pbsmmapi.abstract.helpers import time_zone_aware_now
from pbsmmapi.abstract.models import PBSMMGenericEpisode
from pbsmmapi.api.api import get_PBSMM_record
from pbsmmapi.api.helpers import check_pagination
from pbsmmapi.asset.ingest_asset import process_asset_record
from pbsmmapi.asset.models import Asset
from pbsmmapi.episode.ingest_episode import process_episode_record

PBSMM_EPISODE_ENDPOINT = 'https://media.services.pbs.org/api/v1/episodes/'


class PBSMMEpisode(PBSMMGenericEpisode):
    '''
    These are the fields that are unique to Episode records.
    '''
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


def process_episode_assets(endpoint, this_episode):
    '''
    Scrape assets for this episode, page by page, until there are no more.

    There's probably a way to abstract this so that for all the *-Asset
    scrapers it would be more DRY.
    '''
    # Handle pagination
    keep_going = True
    scraped_object_ids = []
    while keep_going:
        # This is the endpoint for the 'assets' link (page with list of assets)
        status, json = get_PBSMM_record(endpoint)
        if 'data' in json.keys():
            asset_list = json['data']
        else:
            return

        for item in asset_list:
            object_id = item.get('id')
            scraped_object_ids.append(UUID(object_id))

            try:
                instance = Asset.objects.get(object_id=object_id)
            except Asset.DoesNotExist:
                instance = Asset()

            # For now - borrow from the parent object
            instance.last_api_status = status
            instance.date_last_api_update = time_zone_aware_now()

            instance = process_asset_record(item, instance, origin='episode')
            instance.episode = this_episode
            instance.ingest_on_save = True

            # This needs to be here because otherwise it never updates...
            instance.save()

        keep_going, endpoint = check_pagination(json)

    Asset.objects.filter(episode=this_episode).exclude(
        object_id__in=scraped_object_ids).delete()


# PBS MediaManager API interface

# The interface/access is done with a 'pre_save' receiver based on the value of
# 'ingest_on_save' That way, one can force a reingestion from the Admin OR one
# can do it from a management script by simply getting the record, setting
# ingest_on_save on the record, and calling save().


@receiver(models.signals.pre_save, sender=PBSMMEpisode)
def scrape_PBSMMAPI(sender, instance, **kwargs):
    '''
    This calls the PBS MM API for an Episode and then either saves or creates it.
    '''
    if instance.__class__ is not PBSMMEpisode:
        return

    # If this is a new record, then someone has started it in the Admin using
    # EITHER a legacy COVE ID OR a PBSMM UUID. Depending on which, the
    # retrieval endpoint is slightly different, so this sets the appropriate
    # URL to access.
    if instance.pk and instance.object_id and str(instance.object_id).strip():
        # Object is being edited
        op = 'edit'

    else:  # object is being added
        op = 'create'
        if not instance.object_id:
            return  # do nothing - can't get an ID to look up!

    if op == 'create' or instance.ingest_on_save:
        url = "{}{}/".format(PBSMM_EPISODE_ENDPOINT, instance.object_id)

        # OK - get the record from the API
        (status, json) = get_PBSMM_record(url)

        instance.last_api_status = status
        # Update this record's time stamp (the API has its own)
        instance.date_last_api_update = time_zone_aware_now()

        # If we didn't get a record, abort (there's no sense crying over
        # spilled bits)
        if status != 200:
            return

        # Process the record (code is in ingest.py)
        instance = process_episode_record(json, instance)

        # continue saving, but turn off the ingest_on_save flag
        instance.ingest_on_save = False  # otherwise we could end up in an infinite loop!

    # We're done here - continue with the save() operation
    return instance


@receiver(models.signals.post_save, sender=PBSMMEpisode)
def handle_children(sender, instance, *args, **kwargs):
    '''
    This gets all the children.
    For the case of Episodes, that just means the Episode Assets.

    We ALWAYS get the Assets when the Episode is ingested.
    '''
    if not instance:
        return

    if instance.__class__ is not PBSMMEpisode:
        return

    # ALWAYS GET CHILD ASSETS
    assets_endpoint = instance.json['links'].get('assets')
    if assets_endpoint:
        process_episode_assets(assets_endpoint, instance)

    return
