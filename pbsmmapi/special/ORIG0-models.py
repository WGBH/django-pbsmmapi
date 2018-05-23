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

from .ingest_special import process_special_record

PBSMM_SPECIAL_ENDPOINT = 'https://media.services.pbs.org/api/v1/specials/'

class PBSMMSpecial(PBSMMLightObject):

    show = models.ForeignKey('show.PBSMMShow', related_name = 'specials')
    class Meta:
        verbose_name = 'PBS Media Manager Special'
        verbose_name_plural = 'PBS Media Manager Specials'
        db_table = 'pbsmm_special'
        
    def __unicode__(self):
        return "%s | %s " % (self.object_id, self.title)
        
    def create_table_line(self):
        out = "<tr>"
        out += "\n\t<td>%s</td>" % self.title
        out += "\n\t<td><a href=\"%s\" target=\"_new\">API</a></td>" %  self.api_endpoint
        out += "\n\t<td><a href=\"/admin/special/pbsmmspecial/%d/change/\">Admin</a></td>" % self.id
        out += "\n\t<td>%d</td>" % self.assets.count()
        out += "\n\t<td>%s</td>" % self.date_last_api_update.strftime("%x %X")
        out += "\n\t<td>%s</td>" % self.last_api_status_color()
        out += "\n\t<td>%s</td>" % self.show_publish_status()
        out += "\n</tr>"
        return out
    create_table_line.allow_tags = True

class PBSMMSpecialAsset(PBSMMAbstractAsset):
    special = models.ForeignKey(PBSMMSpecial, related_name='assets')
    
    class Meta:
        verbose_name = 'PBS MM Special Asset'
        verbose_name_plural = 'PBS MM Special Assets'
        db_table = 'pbsmm_special_asset'
        
    def __unicode__(self):
        return "%s: %s" % (self.special.title, self.title)
    
def process_special_assets(endpoint, this_special):
    
    keep_going = True
    while keep_going:
        (status, json) = get_PBSMM_record(endpoint) 
        asset_list = json['data']

        for item in asset_list:
            attrs = item.get('attributes')
            links = item.get('links')
            object_id = item.get('id')
        
            try:
                instance = PBSMMSpecialAsset.objects.get(object_id=object_id)
            except PBSMMSpecialAsset.DoesNotExist:
                instance = PBSMMSpecialAsset()
            
            instance = process_asset_record(item, instance, origin='special')
            instance.special = this_special
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
@receiver(models.signals.pre_save, sender=PBSMMSpecial)
def scrape_PBSMMAPI(sender, instance, **kwargs):
    if instance.__class__ is not PBSMMSpecial:
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

    url = "%s/%s/" % (PBSMM_SPECIAL_ENDPOINT, instance.object_id)

    # OK - get the record from the API
    (status, json) = get_PBSMM_record(url)
    instance.last_api_status = status
    # Update this record's time stamp (the API has its own)
    instance.date_last_api_update = datetime.datetime.now()
    
    # If we didn't get a record, abort (there's no sense crying over spilled bits)
    if status != 200:
        return

    # Process the record (code is in ingest.py)
    instance = process_special_record(json, instance)

    # continue saving, but turn off the ingest_on_save flag
    instance.ingest_on_save = False # otherwise we could end up in an infinite loop!

    # We're done here - continue with the save() operation 
    return
    
    
@receiver(models.signals.post_save, sender=PBSMMSpecial)
def handle_child_objects(sender, instance, *args, **kwargs):
    this_json = instance.json

    # ALWAYS GET CHILD ASSETS
    assets_endpoint = this_json['links'].get('assets')
    if assets_endpoint:
        process_special_assets(assets_endpoint, instance)
            
    return
