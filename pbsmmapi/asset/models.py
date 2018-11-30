# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.db import models
from django.utils.translation import ugettext_lazy as _
from ..abstract.models import PBSMMGenericAsset

from .helpers import check_asset_availability

AVAILABILITY_GROUPS = (
    ('Station Members', 'station_members'),
    ('All Members', 'all_members'),
    ('Public', 'public')
)

# remember the closing slash
PBSMM_ASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/assets/'
PBSMM_LEGACY_ASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/assets/legacy/?tp_media_id='

YES_NO = (
    (1, 'Yes'),
    (0, 'No'),
)


class PBSMMAbstractAsset(PBSMMGenericAsset):
    """
    These are fields unique to Assets.
    Each object model has a *-Asset table, e.g., PBSMMEpisode has PBSMMEpisodeAsset,
    PBSMMShow has PBSShowAsset, etc.

    Aside from the FK reference to the parent, each of these *-Asset models are identical in structure.
    """
    # These fields are unique to Asset
    legacy_tp_media_id = models.BigIntegerField(
        _('COVE ID'),
        null=True, blank=True,
        unique=True,
        help_text='(Legacy TP Media ID)'
    )

    availability = models.TextField(
        _('Availability'),
        null=True, blank=True,
        help_text='JSON serialized Field'
    )

    duration = models.IntegerField(
        _('Duration'),
        null=True, blank=True,
        help_text="(in seconds)"
    )

    object_type = models.CharField(  # This is 'clip', etc.
        _('Object Type'),
        max_length=40,
        null=True, blank=True,
    )

    # CAPTIONS
    has_captions = models.BooleanField(
        _('Has Captions'),
        default=False
    )

    # TAGS, Topics
    tags = models.TextField(
        _('Tags'),
        null=True, blank=True,
        help_text='JSON serialized field'
    )
    topics = models.TextField(
        _('Topics'),
        null=True, blank=True,
        help_text='JSON serialized field'
    )

    # PLAYER FIELDS
    player_code = models.TextField(
        _('Player Code'),
        null=True, blank=True
    )

    # CHAPTERS
    chapters = models.TextField(
        _('Chapters'),
        null=True, blank=True,
        help_text="JSON serialized field"
    )

    content_rating = models.CharField(
        _('Content Rating'),
        max_length=100,
        null=True, blank=True,
    )

    content_rating_description = models.TextField(
        _('Content Rating Description'),
        null=True, blank=True
    )

    # This is a custom field that lies outside of the API.
    #
    # It alloes the content producer to define WHICH Asset is shown on the parental object's Detail page.
    # Since the PBSMM API does not know how to distinguish mutliple "clips" from one another, this is necessary
    # to show a Promo vs. a Short Form video, etc.
    #
    # ... thanks PBS.
    #
    override_default_asset = models.PositiveIntegerField(
        _('Override Default Asset'),
        null=False, choices=YES_NO, default=0
    )

    class Meta:
        abstract = True

    ###
    # Properties and methods
    ###

    def __unicode__(self):
        return "%d | %s (%d) | %s" % (self.pk, self.object_id,
                                      self.legacy_tp_media_id, self.title)

    def __object_model_type(self):
        """
        This handles the correspondence to the "type" field in the PBSMM JSON object.
        Basically this just makes it easy to identify whether an object is an asset or not.
        """
        return 'asset'
    object_model_type = property(__object_model_type)

    def asset_publicly_available(self):
        """
        This is mostly for tables listing Assets in the Admin detail page for ancestral objects:
        e.g., an Episode's page in the Admin has a list of the episode's assets, and this provides
        a simple column to show availability in that list.
        """
        if self.availability:
            a = json.loads(self.availability)
            p = a.get('public', None)
            if p:
                return check_asset_availability(
                    start=p['start'], end=p['end'])[0]
        return None
    asset_publicly_available.short_description = 'Pub. Avail.'
    asset_publicly_available.boolean = True

    def __is_asset_publicly_available(self):
        """
        Am I available to the public?  True/False.
        """
        return self.asset_publicly_available
    is_asset_publicly_available = property(__is_asset_publicly_available)

    def __duration_hms(self):
        """
        Show the asset's duration as #h ##m ##s.
        """
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
        """
        Show the Asset's duration as ##:##:##
        """
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
        """
        Return True/False if the Asset is the "default" Asset for it's parent.
        """
        if self.override_default_asset:
            return True
        else:
            return False
    is_default = property(__is_default)
