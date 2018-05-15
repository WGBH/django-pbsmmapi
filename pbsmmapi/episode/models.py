# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import datetime
import json

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..abstract.models import PBSMMGenericEpisode
from ..abstract.helpers import get_canonical_image

from pbsmmapi.api.api import get_PBSMM_record
from .ingest import process_episode_record

#from ..asset.models import AssetEpisodeRelation

PBSMM_EPISODE_ENDPOINT = 'https://media.services.pbs.org/api/v1/episodes/'

class PBSMMEpisode(PBSMMGenericEpisode):
    
    encored_on = models.DateTimeField (
        _('Encored On'),
        blank = True, null = True
    )
    ordinal = models.PositiveIntegerField (
        _('Ordinal'),
        blank = True, null = True
    )
    segment = models.CharField (
        _('Segment'),
        max_length = 200,
        blank = True, null = True
    )
    
    ###### RELATIONSHIP INGESTION FLAGS
    ingest_related_assets = models.BooleanField (
        _('Ingest Related Assets'),
        default = False,
        help_text = 'If true, then will scrape assets from the PBSMM API on save()'
    )
    
    class Meta:
        verbose_name = 'PBS Media Manager Episode'
        verbose_name_plural = 'PBS Media Manager Episodes'
        #app_label = 'pbsmmapi'
        db_table = 'pbsmm_episode'
        
    def __unicode__(self):
        return "%s | %s (%s) " % (self.object_id, self.title, self.premiered_on)
        
    def __object_model_type(self):
    # This handles the correspondence to the "type" field in the PBSMM JSON object
        return 'episode'
    object_model_type = property(__object_model_type)
    
    def __get_canonical_image(self):
        if self.images:
            image_list = json.loads(self.images)
            return get_canonical_image(image_list)
        else:
            return None
    canonical_image = property(__get_canonical_image)

    def canonical_image_tag(self):
        if self.canonical_image and "http" in self.canonical_image:
            return "<img src=\"%s\">" % self.canonical_image
        return None
    canonical_image_tag.allow_tags = True
    
    ### RELATIONSHIP DISPLAY
    def show_related_assets(self):
        related_assets = self.related_asset_list.all()
        if related_assets and len(related_assets) > 0:
            foo = '<table><tr><th>Asset Type</th><th>Link to Admin</th><th>Link to API Record</th><th>Last API Status</th></tr>'
            for item in related_assets:
                a = item.asset
                foo += '<tr><td>%s</td><td><a href="/admin/pbsmmapi/pbsmmasset/%d/">%s</a></td><td>%s</td><td>%s</td></tr>' %\
                    (a.object_type, a.pk, a.title, a.link_to_api_record_link(), a.last_api_status_color())
            foo += "</table>"
            return foo
        else:
            return "<b>No related assets</b>"
    show_related_assets.allow_tags = True
    show_related_assets.short_description = 'Related Assets'


#######################################################################################################################
###################
###################  PBS MediaManager API interface
###################
#######################################################################################################################
##### The interface/access is done with a 'pre_save' receiver based on the value of 'ingest_on_save'
#####
##### That way, one can force a reingestion from the Admin OR one can do it from a management script
##### by simply getting the record, setting ingest_on_save on the record, and calling save().
#####

@receiver(models.signals.pre_save, sender=PBSMMEpisode)
def scrape_PBSMMAPI(sender, instance, **kwargs):

    if instance.__class__ is not PBSMMEpisode:
        return

    # If this is a new record, then someone has started it in the Admin using EITHER a legacy COVE ID
    # OR a PBSMM UUID.   Depending on which, the retrieval endpoint is slightly different, so this sets
    # the appropriate URL to access.
    if instance.pk and instance.object_id and str(instance.object_id).strip():
        # Object is being edited
        op = 'edit'
        #if not instance.ingest_on_save:
        #    return # do nothing - can't get an ID to look up!

    else: # object is being added
        op = 'create'
        if not instance.object_id:
            return # do nothing - can't get an ID to look up!


    if op == 'create' or instance.ingest_on_save:
        url = "%s/%s/" % (PBSMM_EPISODE_ENDPOINT, instance.object_id)

        # OK - get the record from the API
        (status, json) = get_PBSMM_record(url)

        instance.last_api_status = status
        # Update this record's time stamp (the API has its own)
        instance.date_last_api_update = datetime.datetime.now()
    
        # If we didn't get a record, abort (there's no sense crying over spilled bits)
        if status != 200:
            return

        # Process the record (code is in ingest.py)
        instance = process_episode_record(json, instance)

        # continue saving, but turn off the ingest_on_save flag
        instance.ingest_on_save = False # otherwise we could end up in an infinite loop!

    #instance.ingest_related_assets = False
    # We're done here - continue with the save() operation 
    return instance
    
#def foo(instance):
#    if instance.ingest_related_assets:
#        if instance.pk:
#            new_related_assets_list = process_related_assets(json)
#            known_ids = []
#            known_assets = AssetEpisodeRelation.objects.filter(episode__id=instance.pk)
#            for a in known_assets:
#                knowns_ids.append(a.pk)
#                
#            if len(new_related_assets_list) > 0:
#                for item in new_related_asset_list:
#                    if item not in known_ids:
#                        x = AssetEpisodeRelation(episode=instance, asset=)
    
def process_related_assets(obj):
    links = obj['links']
    related_assets_endpoint = links.get('assets', None)
    new_related_assets = []
    (status, json) = get_PBSMM_record(related_assets_endpoint)
    if status == 200:
        asset_list = json['data']

        for asset in asset_list:
            asset_id = asset.get('id', None)
            (op, asset_pk) = ingest_related_asset(asset_id)                    
            if op == 'new' and asset_pk:
                new_related_assets.append(asset_pk)