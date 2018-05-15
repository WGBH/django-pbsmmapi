# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import datetime
import json

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..abstract.models import PBSMMGenericSeason
from ..abstract.helpers import get_canonical_image

from pbsmmapi.api.api import get_PBSMM_record
from .ingest import process_season_record

PBSMM_SEASON_ENDPOINT = 'https://media.services.pbs.org/api/v1/seasons/'

class PBSMMSeason(PBSMMGenericSeason):
    
    ordinal = models.PositiveIntegerField (
        _('Ordinal'),
        null = True, blank = True
    )
    
    class Meta:
        verbose_name = 'PBS Media Manager Season'
        verbose_name_plural = 'PBS Media Manager Seasons'
        #app_label = 'pbsmmapi'
        db_table = 'pbsmm_season'
        
    def __unicode__(self):
        return "%s | %s " % (self.object_id, self.title)

    def __object_model_type(self):
    # This handles the correspondence to the "type" field in the PBSMM JSON object
        return 'season'
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
