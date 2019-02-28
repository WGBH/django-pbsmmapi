# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from uuid import UUID

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse

from ..abstract.gatekeeper import can_object_page_be_shown
from ..abstract.helpers import time_zone_aware_now
from ..abstract.models import PBSMMGenericShow

from ..api.api import get_PBSMM_record
from ..api.helpers import check_pagination

from ..asset.ingest_asset import process_asset_record
from ..asset.models import PBSMMAbstractAsset

from .ingest_show import process_show_record
from .ingest_children import process_seasons, process_specials

PBSMM_SHOW_ENDPOINT = 'https://media.services.pbs.org/api/v1/shows/'


class PBSMMAbstractShow(PBSMMGenericShow):

    ingest_seasons = models.BooleanField(
        _('Ingest Seasons'),
        default=False,
        help_text='Also ingest all Seasons'
    )
    ingest_specials = models.BooleanField(
        _('Ingest Specials'),
        default=False,
        help_text='Also ingest all Specials'
    )
    ingest_episodes = models.BooleanField(
        _('Ingest Episodes'),
        default=False,
        help_text='Also ingest all Episodes (for each Season)'
    )

    class Meta:
        verbose_name = 'PBS MM Show'
        verbose_name_plural = 'PBS MM Shows'
        # app_label = 'pbsmmapi'
        db_table = 'pbsmm_show'
        abstract = True

    def get_absolute_url(self):
        return reverse('show-detail', args=[self.slug])

    def __unicode__(self):
        if self.title:
            return self.title
        else:
            return "ID %d: unknown" % self.id

    def __object_model_type(self):
        # This handles the correspondence to the "type" field in the PBSMM JSON
        # object
        return 'show'
    object_model_type = property(__object_model_type)

    def __available_to_public(self):
        return can_object_page_be_shown(None, self)
    available_to_public = property(__available_to_public)


class PBSMMShow(PBSMMAbstractShow):
    pass


class PBSMMShowAsset(PBSMMAbstractAsset):
    show = models.ForeignKey(
        PBSMMShow, related_name='assets',
        on_delete=models.CASCADE,  # required for Django 2.0
    )

    class Meta:
        verbose_name = 'PBS MM Show - Asset'
        verbose_name_plural = 'PBS MM Shows - Assets'
        db_table = 'pbsmm_show_asset'

    def __unicode__(self):
        return "%s: %s" % (self.show, self.title)


def process_show_assets(endpoint, this_show):
    keep_going = True
    scraped_object_ids = []
    while keep_going:
        (status, json) = get_PBSMM_record(endpoint)
        data = json['data']

        for item in data:
            object_id = item.get('id')
            scraped_object_ids.append(UUID(object_id))

            try:
                instance = PBSMMShowAsset.objects.get(object_id=object_id)
            except PBSMMShowAsset.DoesNotExist:
                instance = PBSMMShowAsset()

            instance = process_asset_record(item, instance, origin='show')

            # For now - borrow from the parent object
            instance.last_api_status = status
            instance.date_last_api_update = time_zone_aware_now()

            instance.show = this_show
            instance.ingest_on_save = True

            # This needs to be here because otherwise it never updates...
            instance.save()

        (keep_going, endpoint) = check_pagination(json)

    for asset in PBSMMShowAsset.objects.filter(show=this_show):
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


@receiver(models.signals.pre_save, sender=PBSMMShow)
def scrape_PBSMMAPI(sender, instance, **kwargs):
    if instance.__class__ is not PBSMMShow:
        return

    # If this is a new record, then someone has started it in the Admin using
    # a PBSMM UUID.   Depending on which, the retrieval endpoint is slightly different, so this sets
    # the appropriate URL to access.
    if instance.pk and instance.slug and str(instance.slug).strip():
        # Object is being edited
        if not instance.ingest_on_save:
            return  # do nothing - can't get an ID to look up!

    else:  # object is being added
        if not instance.slug:
            return  # do nothing - can't get an ID to look up!

    url = "{}{}/".format(PBSMM_SHOW_ENDPOINT, instance.slug)

    # OK - get the record from the API
    (status, json) = get_PBSMM_record(url)

    instance.last_api_status = status
    # Update this record's time stamp (the API has its own)
    instance.date_last_api_update = time_zone_aware_now()

    # If we didn't get a record, abort (there's no sense crying over spilled
    # bits)
    if status != 200:
        return

    # Process the record (code is in ingest.py)
    instance = process_show_record(json, instance)

    # continue saving, but turn off the ingest_on_save flag
    instance.ingest_on_save = False  # otherwise we could end up in an infinite loop!

    # We're done here - continue with the save() operation
    return


@receiver(models.signals.post_save, sender=PBSMMShow)
def handle_child_objects(sender, instance, *args, **kwargs):

    if instance.last_api_status != 200:
        return
    this_json = instance.json

    # ALWAYS GET CHILD ASSETS
    assets_endpoint = this_json['links'].get('assets')
    if assets_endpoint:
        process_show_assets(assets_endpoint, instance)

    if instance.ingest_seasons:
        seasons_endpoint = this_json['links'].get('seasons')
        if seasons_endpoint:
            process_seasons(seasons_endpoint, instance)

    if instance.ingest_specials:
        specials_endpoint = this_json['links'].get('specials')
        if specials_endpoint:
            process_specials(specials_endpoint, instance)

    # This is a tricky way to unset ingest_seasons without calling save()
    rec = PBSMMShow.objects.filter(pk=instance.id)
    rec.update(
        ingest_seasons=False,
        ingest_specials=False,
        ingest_episodes=False)
    return
