# -*- coding: utf-8 -*-
import json

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class GenericObjectManagement(models.Model):
    date_created = models.DateTimeField(
        _('Created On'),
        auto_now_add=True,
        help_text='Not set by API',
    )
    date_last_api_update = models.DateTimeField(
        _('Last API Retrieval'),
        help_text='Not set by API',
        null=True,
    )
    ingest_on_save = models.BooleanField(
        _('Ingest on Save'),
        default=False,
        help_text='If true, then will update values from the PBSMM API on save()'
    )
    last_api_status = models.PositiveIntegerField(
        _('Last API Status'),
        null=True,
        blank=True,
    )
    json = models.JSONField(
        _('JSON'),
        null=True,
        blank=True,
        help_text='This is the last JSON uploaded.',
    )

    def last_api_status_color(self):
        template = '<b><span style="color:#%s;">%d</span></b>'
        if self.last_api_status:
            if self.last_api_status == 200:
                return mark_safe(template % ('0c0', self.last_api_status))
            return mark_safe(template % ('f00', self.last_api_status))
        return mark_safe(self.last_api_status)

    last_api_status_color.short_description = 'Status'

    class Meta:
        abstract = True


class PBSMMObjectID(models.Model):
    '''
    In most parallel universes, we'd use this as the PRIMARY KEY. However,
    given the periodic necessity of having to EDIT records or manipulate them
    in the database, the issue of having to juggle 32-length random characters
    instead of a nice integer ID would be a PITA.

    So I'm being "un-pure".  Sue me.   RAD 31-Jan-2018
    '''
    object_id = models.UUIDField(
        _('Object ID'),
        unique=True,
        null=True,
        blank=True  # does this work?
    )

    class Meta:
        abstract = True


class PBSObjectMetadata(models.Model):
    '''Exists for all objects'''
    api_endpoint = models.URLField(
        _('Link to API Record'),
        null=True,
        blank=True,
        help_text='Endpoint to original record from the API'
    )

    def api_endpoint_link(self):
        # This just makes the field clickable in the Admin (why cut and paste
        # when you can click?)
        return mark_safe(
            f'<a href="{self.api_endpoint}" target="_new">{self.api_endpoint}</a>'
        )

    api_endpoint_link.short_description = 'Link to API'

    class Meta:
        abstract = True


class PBSMMObjectTitle(models.Model):
    '''Exists for all objects'''
    title = models.CharField(_('Title'), max_length=200, null=True, blank=True)

    class Meta:
        abstract = True


class PBSMMObjectSortableTitle(models.Model):
    '''
    Exists for all objects EXCEPT Collection - so we have to separate it
    (I don't understand why the API just didn't create this across records...)
    '''
    title_sortable = models.CharField(
        _('Sortable Title'), max_length=200, null=True, blank=True
    )

    class Meta:
        abstract = True


class PBSMMObjectSlug(models.Model):
    '''
    These exist for all objects EXCEPT Season
    (see note/whine on PBSMMObjectSortableTitle)
    '''
    slug = models.SlugField(
        _('Slug'),
        unique=True,
        max_length=200,
    )

    class Meta:
        abstract = True


class PBSMMObjectTitleSortableTitle(PBSMMObjectTitle, PBSMMObjectSortableTitle):
    '''Lump them together'''
    class Meta:
        abstract = True


class PBSMMObjectDescription(models.Model):
    '''These exist for all Objects'''
    description_long = models.TextField(_('Long Description'))
    description_short = models.TextField(_('Short Description'))

    class Meta:
        abstract = True


class PBSMMObjectDates(models.Model):
    '''This exists for all objects'''
    updated_at = models.DateTimeField(
        _('Updated At'),
        null=True,
        blank=True,
        help_text='API record modified date',
    )

    class Meta:
        abstract = True


class PBSMMBroadcastDates(models.Model):
    '''
    premiered_on exists for Episode, Franchise, Show, and Special but NOT
    Collection or Season

    encored_on ONLY exists for Episode so we might have to
    split them up
    '''
    premiered_on = models.DateTimeField(_('Premiered On'), null=True, blank=True)

    @property
    def short_premiere_date(self):
        return self.premiered_on.strftime('%x')

    class Meta:
        abstract = True


class PBSMMNOLA(models.Model):
    '''
    This exists for Episode, Franchise, and Special but NOT for Collection,
    Show, or Season
    '''
    nola = models.CharField(_('NOLA Code'), max_length=8, null=True, blank=True)

    class Meta:
        abstract = True


# Here's something annoying: images only exists for Asset, but the other object
# have images, just called something else. I have to decide whether I will
# abide by this nomenclature or not
class PBSMMImage(models.Model):
    images = models.TextField(
        _('Images'),
        null=True,
        blank=True,
        help_text='JSON serialized field',
    )

    def pretty_image_list(self):
        if self.images:
            image_list = json.loads(self.images)
            out = '<table width=\"100%\">'
            out += '<tr><th>Profile</th><th>Updated At</th></tr>'
            for image in image_list:
                out += '\n<tr>'
                out += f'<td><a href="{image["image"]}" target="_new">'
                out += f'{image["profile"]}</a></td>'
                out += f'<td>{image["updated_at"]}</td>'
                out += '</tr>'
            out += '</table>'
            return mark_safe(out)
        return None

    pretty_image_list.short_description = 'Image List'

    class Meta:
        abstract = True


class PBSMMFunder(models.Model):
    funder_message = models.TextField(
        _('Funder Message'),
        null=True,
        blank=True,
        help_text='JSON serialized field',
    )

    class Meta:
        abstract = True


class PBSMMPlayerMetadata(models.Model):
    is_excluded_from_dfp = models.BooleanField(_('Is excluded from DFP'), default=False)

    can_embed_player = models.BooleanField(_('Can Embed Player'), default=False)

    class Meta:
        abstract = True


class PBSMMLinks(models.Model):
    links = models.TextField(
        _('Links'), null=True, blank=True, help_text='JSON serialized field'
    )

    class Meta:
        abstract = True


class PBSMMPlatforms(models.Model):
    platforms = models.TextField(
        _('Platforms'), null=True, blank=True, help_text='JSON serialized field'
    )

    class Meta:
        abstract = True


class PBSMMWindows(models.Model):
    windows = models.TextField(
        _('Windows'), null=True, blank=True, help_text='JSON serialized field'
    )

    class Meta:
        abstract = True


class PBSMMGeo(models.Model):
    # countries --- hold off until needed
    geo_profile = models.TextField(
        _('Geo Profile'), null=True, blank=True, help_text='JSON serialized field'
    )

    class Meta:
        abstract = True


class PBSMMGoogleTracking(models.Model):
    ga_page = models.CharField(_('GA Page Tag'), max_length=40, null=True, blank=True)
    ga_event = models.CharField(_('GA Event Tag'), max_length=40, null=True, blank=True)

    class Meta:
        abstract = True


class PBSMMGenre(models.Model):
    genre = models.TextField(
        _('Genre'),
        null=True,
        blank=True,
        help_text='JSON Serialized Field',
    )

    class Meta:
        abstract = True


class PBSMMEpisodeSeason(models.Model):
    episode_count = models.PositiveIntegerField(
        _('Episode Count'),
        null=True,
        blank=True,
    )
    display_episode_number = models.BooleanField(
        _('Display Episode Number'),
        default=False,
    )
    sort_episodes_descending = models.BooleanField(
        _('Sort Episodes Descending'),
        default=False,
    )
    ordinal_season = models.BooleanField(
        _('Ordinal Season'),
        default=True,
    )

    class Meta:
        abstract = True


class PBSMMLanguage(models.Model):
    language = models.CharField(
        _('Language'),
        max_length=10,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PBSMMAudience(models.Model):
    audience = models.TextField(
        _('Audience'),
        null=True,
        blank=True,
        help_text='JSON Serialized Field',
    )

    class Meta:
        abstract = True


class PBSMMHashtag(models.Model):
    hashtag = models.CharField(
        _('Hashtag'),
        max_length=100,
        null=True,
        blank=True,
    )

    class Meta:
        abstract = True


class PBSMMGenericObject(
        PBSMMObjectID,
        PBSMMObjectTitleSortableTitle,
        PBSMMObjectDescription,
        PBSMMObjectDates,
        GenericObjectManagement,
        PBSObjectMetadata,
):
    class Meta:
        abstract = True


class PBSMMGenericAsset(
        PBSMMGenericObject,
        PBSMMObjectSlug,
        PBSMMImage,
        PBSMMFunder,
        PBSMMPlayerMetadata,
        PBSMMLinks,
        PBSMMGeo,
        PBSMMPlatforms,
        PBSMMWindows,
        PBSMMLanguage,
):
    class Meta:
        abstract = True


class PBSMMGenericRemoteAsset(PBSMMGenericObject):
    class Meta:
        abstract = True


class PBSMMGenericShow(
        PBSMMGenericObject,
        PBSMMObjectSlug,
        PBSMMLinks,
        PBSMMNOLA,
        PBSMMHashtag,
        PBSMMImage,
        PBSMMGenre,
        PBSMMFunder,
        PBSMMPlayerMetadata,
        PBSMMGoogleTracking,
        PBSMMEpisodeSeason,
        PBSMMPlatforms,
        PBSMMAudience,
        PBSMMBroadcastDates,
        PBSMMLanguage,
):
    class Meta:
        abstract = True


class PBSMMGenericEpisode(
        PBSMMGenericObject,
        PBSMMObjectSlug,
        PBSMMFunder,
        PBSMMLanguage,
        PBSMMBroadcastDates,
        PBSMMNOLA,
        PBSMMLinks,
):
    class Meta:
        abstract = True


class PBSMMGenericSeason(PBSMMGenericObject, PBSMMLinks, PBSMMImage):
    class Meta:
        abstract = True


class PBSMMGenericSpecial(
        PBSMMGenericObject,
        PBSMMObjectSlug,
        PBSMMLanguage,
        PBSMMBroadcastDates,
        PBSMMNOLA,
        PBSMMLinks,
):
    class Meta:
        abstract = True


class PBSMMGenericCollection(PBSMMGenericObject, PBSMMObjectSlug, PBSMMImage):
    # There is no sortable title field - it is allowed in the model purely out
    # of laziness since abstracting it out from PBSGenericObject would be
    # more-complicated than leaving it in. PLUS I suspect that eventually it'll
    # be added...
    class Meta:
        abstract = True


class PBSMMGenericFranchise(
        PBSMMGenericObject,
        PBSMMObjectSlug,
        PBSMMFunder,
        PBSMMNOLA,
        PBSMMBroadcastDates,
        PBSMMImage,
        PBSMMPlatforms,
        PBSMMLinks,
        PBSMMHashtag,
        PBSMMGoogleTracking,
        PBSMMGenre,
        PBSMMPlayerMetadata,
):
    # There is no can_embed_player field - again, laziness (see above)
    class Meta:
        abstract = True
