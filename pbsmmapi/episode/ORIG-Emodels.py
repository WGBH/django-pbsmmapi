from __future__ import unicode_literals
import requests
import datetime
import json

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..abstract.models import PBSMMLightObject
from ..api.api import get_PBSMM_record
from ..api.helpers import check_pagination

from ..asset.models import PBSMMAbstractAsset
from ..asset.ingest_asset import process_asset_record

from .ingest_episode import process_episode_record

PBSMM_EPISODE_ENDPOINT = 'https://media.services.pbs.org/api/v1/episodes/'

class PBSMMEpisode(PBSMMLightObject):
    ordinal = models.PositiveIntegerField (
        _('Ordinal'),
        blank = True, null = True
    )
    
    season = models.ForeignKey ('season.PBSMMSeason',  related_name='episodes')
    
    class Meta:
        verbose_name = 'PBS Media Manager Episode'
        verbose_name_plural = 'PBS Media Manager Episodes'
        #app_label = 'pbsmmapi'
        db_table = 'pbsmm_episode'
        
    def __unicode__(self):
        return "%s | %s " % (self.object_id, self.title)
        
    def episode_code(self):
        return "%s-%02d%02d" % (self.season.show.slug, self.season.ordinal, self.ordinal)
    episode_code.short_description = 'Ep #'
    
    def create_table_line(self):
        out = "<tr>"
        out += "\t<td></td>"
        out += "\n\t<td>%02d%02d:</td>" % (self.season.ordinal, self.ordinal)
        out += "\n\t<td>%s</td>" % self.title
        out += "\n\t<td><a href=\"%s\" target=\"_new\">API</a></td>" % self.api_endpoint
        out += "\n\t<td><a href=\"/admin/episode/pbsmmepisode/%d/change/\">Admin</a></td>" % self.id
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        out += "\n\t<td>%s</td></tr>" % self.show_publish_status()
        return out
    create_table_line.allow_tags = True
    
class PBSMMEpisodeAsset(PBSMMAbstractAsset):
    episode = models.ForeignKey(PBSMMEpisode, related_name='assets')
    
        
    class Meta:
        verbose_name = 'PBS MM Episode Asset'
        verbose_name_plural = 'PBS MM Episode Assets'
        db_table = 'pbsmm_episode_asset'
        
    def __unicode__(self):
        return "%s: %s" % (self.episode.title, self.title)
        

def process_episode_assets(endpoint, this_episode):
    
    keep_going = True
    while keep_going:
        (status, json) = get_PBSMM_record(endpoint) # This is the endpoint for the 'assets' link (page with list of assets)
        asset_list = json['data']

        for item in asset_list:
            attrs = item.get('attributes')
            links = item.get('links')
            object_id = item.get('id')
        
            try:
                instance = PBSMMEpisodeAsset.objects.get(object_id=object_id)
            except PBSMMEpisodeAsset.DoesNotExist:
                instance = PBSMMEpisodeAsset()
                
            instance.last_api_status = status
            ## Update this record's time stamp (the API has its own)
            instance.date_last_api_update = datetime.datetime.now()
            
            instance = process_asset_record(item, instance, origin='episode')
            instance.episode = this_episode
            instance.ingest_on_save = True
            
            # This needs to be here because otherwise it never updates...
            instance.save()
        
        (keep_going, endpoint) = check_pagination(json)
        
    return

    
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
    
#
@receiver(models.signals.post_save, sender=PBSMMEpisode)
def handle_children(sender, instance, *args, **kwargs):
            
    # ALWAYS GET CHILD ASSETS
    assets_endpoint = instance.json['links'].get('assets')
    if assets_endpoint:
        process_episode_assets(assets_endpoint, instance)
    
    return