# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import requests
import datetime
import json

from django.db import models
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _

from ..abstract.models import PBSMMGenericEpisode
from ..asset.helpers import get_canonical_image
from ..api.api import get_PBSMM_record
from .ingest import process_episode_record

PBSMM_REMOTEASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/episodes/'

class PBSMMEpisode(PBSMMGenericEpisode):
    
    encored_on = models.DateTimeField (
        _('Encored On'),
        blank = True, null = True
    )
    
    class Meta:
        verbose_name = 'PBS Medio Manager Episode'
        verbose_name_plural = 'PBS Media Manager Episodes'
        
    def __unicode__(self):
        return "%d: %s | %s (%s) " % (self.id, self.object_id, self.title, self.premiered_on)
        

    def __get_canonical_image(self):
        if self.images:
            image_list = json.loads(self.images)
            return get_canonical_image(image_list)
        else:
            return None
    canonical_image = property(__get_canonical_image)

    def canonical_image_tag(self):
        if "http" in self.canonical_image:
            return "<img src=\"%s\">" % self.canonical_image
        return None
    canonical_image_tag.allow_tags = True
        
        