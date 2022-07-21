# -*- coding: utf-8 -*-
from django.db import models
from django.utils.translation import gettext_lazy as _
from pbsmmapi.abstract.models import PBSMMGenericAsset
from pbsmmapi.asset.helpers import check_asset_availability

AVAILABILITY_GROUPS = (
    ('Station Members', 'station_members'),
    ('All Members', 'all_members'),
    ('Public', 'public'),
)

PBSMM_BASE_URL = 'https://media.services.pbs.org/'
PBSMM_ASSET_ENDPOINT = f'{PBSMM_BASE_URL}api/v1/assets/'
PBSMM_LEGACY_ASSET_ENDPOINT = f'{PBSMM_ASSET_ENDPOINT}legacy/?tp_media_id='


class Asset(PBSMMGenericAsset):
    '''
    These are fields unique to Assets.
    Each object model has a *-Asset table, e.g., PBSMMEpisode has PBSMMEpisodeAsset,
    PBSMMShow has PBSShowAsset, etc.

    Aside from the FK reference to the parent, each of these *-Asset models are
    identical in structure.
    '''

    # These fields are unique to Asset
    legacy_tp_media_id = models.BigIntegerField(
        _('COVE ID'),
        null=True,
        blank=True,
        unique=True,
        help_text='(Legacy TP Media ID)',
    )

    availability = models.JSONField(
        _('Availability'),
        null=True,
        blank=True,
        help_text='JSON serialized Field',
    )

    duration = models.IntegerField(
        _('Duration'),
        null=True,
        blank=True,
        help_text='(in seconds)',
    )

    object_type = models.CharField(  # This is 'clip', etc.
        _('Object Type'),
        max_length=40,
        null=True,
        blank=True,
    )

    # CAPTIONS
    has_captions = models.BooleanField(
        _('Has Captions'),
        default=False,
    )

    # TAGS, Topics
    tags = models.JSONField(
        _('Tags'),
        null=True,
        blank=True,
        help_text='JSON serialized field',
    )
    topics = models.JSONField(
        _('Topics'),
        null=True,
        blank=True,
        help_text='JSON serialized field',
    )

    # PLAYER FIELDS
    player_code = models.TextField(
        _('Player Code'),
        null=True,
        blank=True,
    )

    # CHAPTERS
    chapters = models.JSONField(
        _('Chapters'),
        null=True,
        blank=True,
        help_text='JSON serialized field',
    )

    content_rating = models.CharField(
        _('Content Rating'),
        max_length=100,
        null=True,
        blank=True,
    )

    content_rating_description = models.TextField(
        _('Content Rating Description'),
        null=True,
        blank=True,
    )

    # Relationships

    episode = models.ForeignKey(
        'episode.PBSMMEpisode',
        null=True,
        blank=True,
        related_name='assets',
        on_delete=models.SET_NULL,
    )

    season = models.ForeignKey(
        'season.PBSMMSeason',
        null=True,
        blank=True,
        related_name='assets',
        on_delete=models.SET_NULL,
    )

    show = models.ForeignKey(
        'show.PBSMMShow',
        null=True,
        blank=True,
        related_name='assets',
        on_delete=models.SET_NULL,
    )

    special = models.ForeignKey(
        'special.PBSMMSpecial',
        null=True,
        blank=True,
        related_name='assets',
        on_delete=models.SET_NULL,
    )

    # Properties and methods
    @property
    def object_model_type(self):
        '''
        This handles the correspondence to the "type" field in the PBSMM JSON
        object. Basically this just makes it easy to identify whether an object
        is an asset or not.
        '''
        return 'asset'

    def asset_publicly_available(self):
        '''
        This is mostly for tables listing Assets in the Admin detail page for
        ancestral objects: e.g., an Episode's page in the Admin has a list of
        the episode's assets, and this provides a simple column to show
        availability in that list.
        '''
        if self.availability:
            public_window = self.availability.get('public', None)
            if public_window:
                return check_asset_availability(
                    start=public_window['start'],
                    end=public_window['end'],
                )[0]
        return None

    asset_publicly_available.short_description = 'Pub. Avail.'
    asset_publicly_available.boolean = True

    @property
    def duration_hms(self):
        # TODO rewrite this
        '''
        Show the asset's duration as #h ##m ##s.
        '''
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

    @property
    def formatted_duration(self):
        # TODO rewrite this
        '''
        Show the Asset's duration as ##:##:##
        '''
        if self.duration:
            seconds = self.duration
            hours = seconds // 3600
            seconds %= 3600
            minutes = seconds // 60
            seconds %= 60
            return '%d:%02d:%02d' % (hours, minutes, seconds)
        return ''

    # @property
    # def dynamic_field_list(self):
    #     return self.json.keys()
    #
    # def __getattr__(self, item):
    #     try:
    #         return self.json[item]
    #     except KeyError:
    #         raise AttributeError(f'{item} not present')

    def __str__(self):
        return f'{self.pk} ' \
               f'| {self.object_id} ({self.legacy_tp_media_id}) ' \
               f'| {self.title}'
