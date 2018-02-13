# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import datetime
import json

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..abstract.models import PBSMMGenericAsset
from ..api.api import get_PBSMM_record
    
from .ingest import process_asset_record
from .helpers import check_asset_availability
from ..abstract.helpers import get_canonical_image

AVAILABILITY_GROUPS = (
    ('Station Members', 'station_members'),
    ('All Members', 'all_members'),
    ('Public', 'public')
)

PBSMM_ASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/assets/' # remember the closing slash
PBSMM_LEGACY_ASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/assets/legacy/?tp_media_id='

class PBSMMAsset(PBSMMGenericAsset):
    
#### These fields are unique to Asset
    legacy_tp_media_id = models.BigIntegerField (
        _('COVE ID'),
        null = True, blank = True,
        unique = True, 
        help_text = '(Legacy TP Media ID)'
    )
    
    availability = models.TextField (
        _('Availability'),
        null = True, blank = True,
        help_text = 'JSON serialized Field'
    )
    
    duration = models.IntegerField (
        _('Duration'),
        null = True, blank = True,
        help_text = "(in seconds)"
    )

    object_type = models.CharField (  # This is 'clip', etc. 
        _('Object Type'),
        max_length = 40,
        null = True, blank = True,
    )
    
    ##### CAPTIONS
    has_captions = models.BooleanField (
        _('Has Captions'),
        default = False
    )
    
    ##### TAGS, Topics
    tags = models.TextField (
        _('Tags'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )
    topics = models.TextField (
        _('Topics'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )
    
    ##### PLAYER FIELDS
    player_code = models.TextField (
        _('Player Code'),
        null = True, blank = True
    )
    

    
    # VIDEOS - hold off until needed
    # CAPTIONS - hold off until needed
    # WINDOWS - abstracted
    # PLATFORMS - abstracted
    

    # CHAPTERS
    chapters = models.TextField (
        _('Chapters'),
        null = True, blank = True,
        help_text = "JSON serialized field"
    )
    
    content_rating = models.CharField (
        _('Content Rating'),
        max_length = 100,
        null = True, blank = True,
    )
    
    content_rating_description = models.TextField (
        _('Content Rating Description'),
        null = True, blank = True
    )
    
###
# Foreign Key relationships
###

    # related_promos --- this can be another Asset OR a RemoteAsset
    #remote_related_promos = models.ManyToManyField

    # PARENT TREE
    #   this is a generic relation to one of the other objects


    ##### LINKS TO OTHER OBJECT TYPES
    #
    # FRANCHISE
    # 
    # SEASON
    #
    # SHOW 
    #
    # EPISODE
    # 
    # SPECIAL
    #
    
    class Meta:
        verbose_name = "PBS Media Manager Asset"
        verbose_name_plural = "PBS Media Manager Assets"
        app_label = 'pbsmmapi'
        db_table = 'pbsmm_asset'

###
# Properties and methods
###
    
    def __unicode__(self):
        return "%d | %s (%d) | %s" % (self.pk, self.object_id, self.legacy_tp_media_id, self.title)

    def __object_model_type(self):
    # This handles the correspondence to the "type" field in the PBSMM JSON object
        return 'asset'
    object_model_type = property(__object_model_type)
    
    #def __is_asset_publicly_available(self):
    def asset_publicly_available(self):
        if self.availability:
            a = json.loads(self.availability)
            p = a.get('public', None)
            if p:
                return check_asset_availability(start=p['start'], end=p['end'])[0]
        return None
    asset_publicly_available.short_description = 'Pub. Avail.'
    asset_publicly_available.boolean = True
    
    def __is_asset_publicly_available(self):
        return self.asset_publicly_available
    is_asset_publicly_available = property(__is_asset_publicly_available)

    
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
    
    def save(self, *args, **kwargs):
        #if self.last_api_status != 200:
        #    return
        super(PBSMMAsset, self).save(*args, **kwargs)

    
#######################################################################################################################
###################
###################  PBS MediaManager API interface
###################
#######################################################################################################################
def __get_api_url(op, id):
    if op == 'pbsmm':
        return PBSMM_ASSET_ENDPOINT + str(id) + '/'
    else:
        return PBSMM_LEGACY_ASSET_ENDPOINT + id

##### The interface/access is done with a 'pre_save' receiver based on the value of 'ingest_on_save'
#####
##### That way, one can force a reingestion from the Admin OR one can do it from a management script
##### by simply getting the record, setting ingest_on_save on the record, and calling save().
#####
@receiver(models.signals.pre_save, sender=PBSMMAsset)
def scrape_PBSMMAPI(sender, instance, **kwargs):
    if instance.__class__ is not PBSMMAsset:
        return

    # If this is a new record, then someone has started it in the Admin using EITHER a legacy COVE ID
    # OR a PBSMM UUID.   Depending on which, the retrieval endpoint is slightly different, so this sets
    # the appropriate URL to access.
    if instance.pk is None: 
        if instance.object_id and instance.object_id.strip():
            url = __get_api_url('pbsmm', instance.object_id)
        else:
            if instance.legacy_tp_media_id:
                url = __get_api_url('cove', str(instance.legacy_tp_media_id))
            else:
                return # do nothing - can't get an ID to look up!
                
    # Otherwise, it's an existing record and the UUID should be used
    else: # Editing an existing  record  - do nothing if ingest_on_save is NOT checked!
        if not instance.ingest_on_save:
            return
        url = __get_api_url('pbsmm', instance.object_id)
    
    # OK - get the record from the API
    (status, json) = get_PBSMM_record(url)
    instance.last_api_status = status
    
    # Update this record's time stamp (the API has its own)
    instance.date_last_api_update = datetime.datetime.now()
    
    if status != 200:
        return 
        
    # Process the record (code is in ingest.py)
    instance = process_asset_record(json, instance)
    
    # continue saving, but turn off the ingest_on_save flag
    instance.ingest_on_save = False # otherwise we could end up in an infinite loop!
    
    # We're done here - continue with the save() operation 
    return
    
