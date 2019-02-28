# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from uuid import UUID

from django.db import models
from django.dispatch import receiver
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from ..abstract.helpers import time_zone_aware_now
from ..abstract.models import PBSMMGenericEpisode
from ..api.api import get_PBSMM_record
from ..api.helpers import check_pagination
from ..asset.models import PBSMMAbstractAsset
from ..asset.ingest_asset import process_asset_record

from .ingest_episode import process_episode_record

PBSMM_EPISODE_ENDPOINT = 'https://media.services.pbs.org/api/v1/episodes/'


class PBSMMEpisode(PBSMMGenericEpisode):
    """
    These are the fields that are unique to Episode records.
    """
    encored_on = models.DateTimeField(
        _('Encored On'),
        blank=True, null=True
    )
    ordinal = models.PositiveIntegerField(
        _('Ordinal'),
        blank=True, null=True
    )
    segment = models.CharField(
        _('Segment'),
        max_length=200,
        blank=True, null=True
    )

    # THIS IS THE (required) PARENTAL SEASON
    season = models.ForeignKey(
        'season.PBSMMSeason', related_name='episodes',
        on_delete=models.CASCADE,  # required for Django 2.0

    )

    class Meta:
        verbose_name = 'PBS MM Episode'
        verbose_name_plural = 'PBS MM Episodes'
        # app_label = 'pbsmmapi'
        db_table = 'pbsmm_episode'

    def get_absolute_url(self):
        """
        This is so the Admin can have a "view on site" button
        """
        return reverse('episode-detail', (), {'slug': self.slug})

    def __unicode__(self):
        # return "%s | %s (%s) " % (self.object_id, self.title,
        # self.premiered_on)
        return self.title

    def __object_model_type(self):
        """
        This just returns object "type"
        """
        return 'episode'
    object_model_type = property(__object_model_type)

    def __full_episode_code(self):
        """
        This just formats the Episode as:
            show-XXYY where XX is the season and YY is the ordinal, e.g.,:  roadshow-2305
            for Roadshow, Season 23, Episode 5.

            Useful in lists of episodes that cross Seasons/Shows.
        """
        return "%s-%02d%02d" % (self.season.show.slug,
                                self.season.ordinal, self.ordinal)
    # full_episode_code.short_description = 'Ep #'
    full_episode_code = property(__full_episode_code)

    def short_episode_code(self):
        """
        This is just the Episode "code" without the Show slug, e.g.,  0523 for the 23rd episode of Season 5
        """
        return "%02d%02d" % (self.season.ordinal, self.ordinal)
    short_episode_code.short_description = 'Ep #'

    def __get_nola_code(self):
        if self.nola is None or self.nola == '':
            return None
        if self.season.show.nola is None or self.season.show.nola == '':
            return None
        return "%s-%s" % (self.season.show.nola, self.nola)
    nola_code = property(__get_nola_code)

    def create_table_line(self):
        """
        This just formats a line in a Table of Episodes.
        Used on a Season's admin page and a Show's admin page.
        """
        out = "<tr>"
        out += "\t<td></td>"
        out += "\n\t<td>%02d%02d:</td>" % (self.season.ordinal, self.ordinal)
        out += "\n\t<td><a href=\"/admin/episode/pbsmmepisode/%d/change/\"><b>%s</b></td>" % (
            self.id, self.title)
        out += "\n\t<td><a href=\"%s\" target=\"_new\">API</a></td>" % self.api_endpoint
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        out += "\n\t<td>%s</td></tr>" % self.show_publish_status()
        return mark_safe(out)


class PBSMMEpisodeAsset(PBSMMAbstractAsset):
    """
    These are the Assets associated with an episode.
    """
    episode = models.ForeignKey(
        PBSMMEpisode, related_name='assets',
        on_delete=models.CASCADE,  # required for Django 2.0
    )

    class Meta:
        verbose_name = 'PBS MM Episode Asset'
        verbose_name_plural = 'PBS MM Episodes - Assets'
        db_table = 'pbsmm_episode_asset'

    def __unicode__(self):
        return "%s: %s" % (self.episode.title, self.title)


def process_episode_assets(endpoint, this_episode):
    """
    Scrape assets for this episode, page by page, until there are no more.
    There's probably a way to abstract this so that for all the *-Asset scrapers it would be more DRY.
    """
    # Handle pagination
    keep_going = True
    scraped_object_ids = []
    while keep_going:
        # This is the endpoint for the 'assets' link (page with list of assets)
        (status, json) = get_PBSMM_record(endpoint)
        if 'data' in json.keys():
            asset_list = json['data']
        else:
            return

        for item in asset_list:
            object_id = item.get('id')
            scraped_object_ids.append(UUID(object_id))

            try:
                instance = PBSMMEpisodeAsset.objects.get(object_id=object_id)
            except PBSMMEpisodeAsset.DoesNotExist:
                instance = PBSMMEpisodeAsset()

            # For now - borrow from the parent object
            instance.last_api_status = status
            instance.date_last_api_update = time_zone_aware_now()

            instance = process_asset_record(item, instance, origin='episode')
            instance.episode = this_episode
            instance.ingest_on_save = True

            # This needs to be here because otherwise it never updates...
            instance.save()

        (keep_going, endpoint) = check_pagination(json)

    for asset in PBSMMEpisodeAsset.objects.filter(episode=this_episode):
        if asset.object_id not in scraped_object_ids:
            asset.delete()

    return


##########################################################################
###################
# PBS MediaManager API interface
###################
##########################################################################
# The interface/access is done with a 'pre_save' receiver based on the value of 'ingest_on_save'
#####
# That way, one can force a reingestion from the Admin OR one can do it from a management script
# by simply getting the record, setting ingest_on_save on the record, and calling save().
#####

@receiver(models.signals.pre_save, sender=PBSMMEpisode)
def scrape_PBSMMAPI(sender, instance, **kwargs):
    """
    This calls the PBS MM API for an Episode and then either saves or creates it.
    """
    if instance.__class__ is not PBSMMEpisode:
        return

    # If this is a new record, then someone has started it in the Admin using EITHER a legacy COVE ID
    # OR a PBSMM UUID.   Depending on which, the retrieval endpoint is slightly different, so this sets
    # the appropriate URL to access.
    if instance.pk and instance.object_id and str(instance.object_id).strip():
        # Object is being edited
        op = 'edit'
        # if not instance.ingest_on_save:
        #    return # do nothing - can't get an ID to look up!

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

    # instance.ingest_related_assets = False
    # We're done here - continue with the save() operation
    return instance


@receiver(models.signals.post_save, sender=PBSMMEpisode)
def handle_children(sender, instance, *args, **kwargs):
    """
    This gets all the children.
    For the case of Episodes, that just means the Episode Assets.

    We ALWAYS get the Assets when the Episode is ingested.
    """
    # ALWAYS GET CHILD ASSETS
    assets_endpoint = instance.json['links'].get('assets')
    if assets_endpoint:
        process_episode_assets(assets_endpoint, instance)

    return
