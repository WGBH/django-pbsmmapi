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

from ..asset.ingest_asset import process_asset_record
from ..asset.models import PBSMMAbstractAsset

from .ingest_show import process_show_record
from .ingest_children import process_seasons, process_specials

PBSMM_SHOW_ENDPOINT = 'https://media.services.pbs.org/api/v1/shows/'

class PBSMMShow(PBSMMLightObject):
    ingest_seasons = models.BooleanField (
        _('Ingest Seasons'),
        default = False,
        help_text = 'Also ingest all Seasons'
    )
    ingest_specials = models.BooleanField (
        _('Ingest Specials'),
        default = False,
        help_text = 'Also ingest all Specials'
    )
    ingest_episodes = models.BooleanField (
        _('Ingest Episodes'),
        default = False,
        help_text = 'Also ingest all Episodes (for each Season)'
    )
    
    class Meta:
        verbose_name = 'PBS Media Manager Show'
        verbose_name_plural = 'PBS Media Manager Shows'
        db_table = 'pbsmm_show'

    def __unicode__(self):
        return self.title
        
class PBSMMShowAsset(PBSMMAbstractAsset):
    show = models.ForeignKey(PBSMMShow, related_name='assets')
    
    class Meta:
        verbose_name = 'PBS MM Show Asset'
        verbose_name_plural = 'PBS MM Show Assets'
        db_table = 'pbsmm_show_asset'

    def __unicode__(self):
        return "%s: %s" % (self.show, self.title)
    
def process_show_assets(endpoint, this_show):
    
    keep_going = True
    while keep_going:
        (status, json) = get_PBSMM_record(endpoint) 
        data = json['data']

        for item in data:
            attrs = item.get('attributes')
            links = item.get('links')
            object_id = item.get('id')
        
            try:
                instance = PBSMMShowAsset.objects.get(object_id=object_id)
            except PBSMMShowAsset.DoesNotExist:
                instance = PBSMMShowAsset()
            
            instance = process_asset_record(item, instance, origin='show')

            instance.show = this_show
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
            return # do nothing - can't get an ID to look up!

    else: # object is being added
        if not instance.slug:
            return # do nothing - can't get an ID to look up!

    url = "%s/%s/" % (PBSMM_SHOW_ENDPOINT, instance.slug)

    # OK - get the record from the API
    (status, json) = get_PBSMM_record(url)
    
    instance.last_api_status = status
    # Update this record's time stamp (the API has its own)
    instance.date_last_api_update = datetime.datetime.now()
    
    # If we didn't get a record, abort (there's no sense crying over spilled bits)
    if status != 200:
        return

    # Process the record (code is in ingest.py)
    instance = process_show_record(json, instance)

    # continue saving, but turn off the ingest_on_save flag
    instance.ingest_on_save = False # otherwise we could end up in an infinite loop!
    
    # Note that instance.ingest_seasons is left alone - we unset this (if set) in the post_save @receiver method
    # Ditto ingest_specials
    return
    
@receiver(models.signals.post_save, sender=PBSMMShow)
def handle_child_objects(sender, instance, *args, **kwargs):

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
    rec = PBSMMShow.objects.filter(pk = instance.id)
    rec.update(ingest_seasons = False, ingest_specials = False, ingest_episodes = False)
    return
    