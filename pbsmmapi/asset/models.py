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
    
from .ingest_asset import process_asset_record
from .helpers import check_asset_availability

AVAILABILITY_GROUPS = (
    ('Station Members', 'station_members'),
    ('All Members', 'all_members'),
    ('Public', 'public')
)

PBSMM_ASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/assets/' # remember the closing slash
PBSMM_LEGACY_ASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/assets/legacy/?tp_media_id='

YES_NO = (
    (1, 'Yes'),
    (0, 'No'),
)

class PBSMMAbstractAsset(PBSMMGenericAsset):
    
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
    
    is_default_asset = models.PositiveIntegerField (
        _('Is Default Asset'),
        null = False, choices = YES_NO, default = 0
    )
    
    class Meta:
        abstract = True


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
    
    def __duration_hms(self):
        if self.duration:
            d = self.duration
            hours = d // 3600
            if hours > 0:
                hstr = '%dh' % hours
            else:
                hstr = ''
            d %= 3600
            minutes = d // 60
            if hours > 0:
                mstr = '%02dm' % minutes
            else:
                if minutes > 0:
                    mstr = '%2dm' % minutes
                else:
                    mstr = ''
            seconds = d % 60
            if minutes > 0:
                sstr = '%02ds' % seconds
            else:
                sstr = '%ds' % seconds
            return ' '.join((hstr, mstr, sstr))
        return ''
    duration_hms = property(__duration_hms)
    
    def __formatted_duration(self):
        if self.duration:
            seconds = self.duration
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            return "%d:%02d:%02d" % (hours, minutes, seconds)
        return ''
    formatted_duration = property(__formatted_duration)
    
    def __is_default(self):
        if self.is_default_asset:
            return True
        else:
            return False
    is_default = property(__is_default)
    
    