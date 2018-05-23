# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import datetime
import json

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..abstract.models import PBSMMLightSeasonObject
from ..api.api import get_PBSMM_record
from ..api.helpers import check_pagination
from ..asset.models import PBSMMAbstractAsset
from ..asset.ingest_asset import process_asset_record

from .ingest_season import process_season_record
from .ingest_children import process_episodes

PBSMM_SEASON_ENDPOINT = 'https://media.services.pbs.org/api/v1/seasons/'

class PBSMMSeason(PBSMMLightSeasonObject):
    
    ordinal = models.PositiveIntegerField (
        _('Ordinal'),
        null = True, blank = True
    )

    show = models.ForeignKey('show.PBSMMShow', related_name='seasons')
    
    ingest_episodes = models.BooleanField (
        _('Ingest Epiaodes'),
        default = False,
        help_text = 'Also ingest all Episodes (for each Season)'
    )
    
    class Meta:
        verbose_name = 'PBS Media Manager Season'
        verbose_name_plural = 'PBS Media Manager Seasons'
        db_table = 'pbsmm_season'
    
    def create_table_line(self):
        this_title = "Season %d: %s" % (self.ordinal, self.title)
        out = "<tr style=\"background-color: #ddd;\"><td colspan=\"3\">%s</td><td><a href=\"%s\" target=\"_new\">API</a></td>" % (this_title, self.api_endpoint)
        out += "<td><a href=\"/admin/season/pbsmmseason/%d/change/\">Admin</a></td>" % self.id
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        out += "<td>%s</td></tr>" % self.show_publish_status()
        return out
    create_table_line.allow_tags = True
    
    def __unicode__(self):
        return "%s - Season %d" % (self.show.title, self.ordinal)
        
class PBSMMSeasonAsset(PBSMMAbstractAsset):
    season = models.ForeignKey(PBSMMSeason, related_name='assets')
    
    class Meta:
        verbose_name = 'PBS MM Season Asset'
        verbose_name_plural = 'PBS MM Season Assets'
        db_table = 'pbsmm_season_asset'
        
    def __unicode__(self):
        return "%s: %s" % (self.season.title, self.title)
        
def process_season_assets(endpoint, this_season):
    
    keep_going = True
    while keep_going:
        (status, json) = get_PBSMM_record(endpoint) 
        asset_list = json['data']

        for item in asset_list:
            attrs = item.get('attributes')
            links = item.get('links')
            object_id = item.get('id')
        
            try:
                instance = PBSMMSeasonAsset.objects.get(object_id=object_id)
            except PBSMMSeasonAsset.DoesNotExist:
                instance = PBSMMSeasonAsset()
            
            instance = process_asset_record(item, instance, origin='special')
            instance.season = this_season
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
@receiver(models.signals.pre_save, sender=PBSMMSeason)
def scrape_PBSMMAPI(sender, instance, **kwargs):
    if instance.__class__ is not PBSMMSeason:
        return

    # If this is a new record, then someone has started it in the Admin using EITHER a legacy COVE ID
    # OR a PBSMM UUID.   Depending on which, the retrieval endpoint is slightly different, so this sets
    # the appropriate URL to access.
    if instance.pk and instance.object_id and str(instance.object_id).strip():
        # Object is being edited
        if not instance.ingest_on_save:
            return # do nothing - can't get an ID to look up!

    else: # object is being added
        if not instance.object_id:
            return # do nothing - can't get an ID to look up!

    url = "%s/%s/" % (PBSMM_SEASON_ENDPOINT, instance.object_id)

    # OK - get the record from the API
    (status, json) = get_PBSMM_record(url)
    
    # Save the JSON that's returned so that we can process it later when needed.
    instance.json = json
    instance.last_api_status = status
    # Update this record's time stamp (the API has its own)
    instance.date_last_api_update = datetime.datetime.now()
    
    # If we didn't get a record, abort (there's no sense crying over spilled bits)
    if status != 200:
        return

    # Process the record (code is in ingest.py)
    instance = process_season_record(json, instance)

    # continue saving, but turn off the ingest_on_save flag
    instance.ingest_on_save = False # otherwise we could end up in an infinite loop!

    # We're done here - continue with the save() operation 
    return

@receiver(models.signals.post_save, sender=PBSMMSeason)
def handle_children(sender, instance, *args, **kwargs):
    
    if instance.ingest_episodes:
        # This is the FIRST endpoint - there might be more, depending on pagination!
        episodes_endpoint = instance.json['links'].get('episodes')

        if episodes_endpoint:
            process_episodes(episodes_endpoint, instance)
            
    # ALWAYS GET CHILD ASSETS
    assets_endpoint = instance.json['links'].get('assets')
    if assets_endpoint:
        process_season_assets(assets_endpoint, instance)
            
    # This is a tricky way to unset ingest_seasons without calling save()      
    rec = PBSMMSeason.objects.filter(pk = instance.id)
    rec.update(ingest_episodes = False)
    
    return