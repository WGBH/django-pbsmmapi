# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from pbsmmapi.abstract.gatekeeper import can_object_page_be_shown
from pbsmmapi.abstract.helpers import get_canonical_image
from pbsmmapi.abstract.helpers import get_default_asset
from pbsmmapi.abstract.helpers import is_in_the_future

PUBLISH_STATUS_LIST = (
    (-1, 'NEVER Available'),
    (0, 'USE "Live as of Date"'),
    (1, 'ALWAYS Available'),
)


class GenericObjectManagement(models.Model):
    date_created = models.DateTimeField(
        _('Created On'),
        auto_now_add=True,
        help_text="Not set by API",
    )
    date_last_api_update = models.DateTimeField(
        _('Last API Retrieval'),
        help_text="Not set by API",
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
    json = JSONField(
        _('JSON'),
        null=True,
        blank=True,
        help_text='This is the last JSON uploaded.',
    )

    class Meta:
        abstract = True

    def last_api_status_color(self):
        template = '<b><span style="color:#%s;">%d</span></b>'
        if self.last_api_status:
            if self.last_api_status == 200:
                return mark_safe(template % ('0c0', self.last_api_status))
            return mark_safe(template % ('f00', self.last_api_status))
        return mark_safe(self.last_api_status)

    last_api_status_color.short_description = 'Status'

    def show_publish_status(self):
        if self.publish_status > 0:
            return mark_safe(
                "<span style=\"color: #0c0;\"><b>ALWAYS</b></span> Available"
            )
        if self.publish_status < 0:
            return mark_safe("<span style=\"color: #c00;\"><B>NEVER</b></span> Available")
        # it EQUALS zero
        if self.live_as_of is None:
            return "Never Published"

        dstr = self.live_as_of.strftime("%x")
        if is_in_the_future(self.live_as_of):
            return mark_safe(f'<b>Goes LIVE: {dstr}</b>')

        return mark_safe(f'<B>LIVE</B> <span style="color: #999;">as of: {dstr}</style>')

    show_publish_status.short_description = 'Pub. Status'


class GenericAccessControl(models.Model):
    publish_status = models.IntegerField(
        _('Publish Status'), default=0, null=False, choices=PUBLISH_STATUS_LIST
    )
    # live_as_of starts out as NULL meaning "I am still being worked on" (if
    # publish_status == 0) OR "I have deliberately been pushed live (if
    # publish_status == 1)"

    # if set, then after that date/time the object is "live".

    # This allows content producers to 'set it and forget it'.
    live_as_of = models.DateTimeField(
        _('Live As Of'),
        null=True,
        blank=True,
        help_text='You can Set this to a future date/time to schedule availability.'
    )

    class Meta:
        abstract = True

    def __is_publicly_available(self):
        # can_object_page_be_shown is the site gatekeeper.
        # if the user is None (as is called here) that means "not logged into
        # the Amdin": i.e., the general public.
        return can_object_page_be_shown(None, self)

    is_publicly_available = property(__is_publicly_available)


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


#############################
# FIELDS DEFINITELY ASSOCIATED WITH SOME BUT NOT ALL OBJECTS (confirmed)
#############################


###############
# FIELDS ASSOCIATED WITH BROADCAST OR PREMIERE (on whatever platform)
###############
class PBSMMBroadcastDates(models.Model):
    '''
    premiered_on exists for Episode, Franchise, Show, and Special but NOT
    Collection or Season encored_on ONLY exists for Episode so we might have to
    split them up
    '''
    premiered_on = models.DateTimeField(_('Premiered On'), null=True, blank=True)

    def __short_premiere_date(self):
        return self.premiered_on.strftime('%x')

    short_premiere_date = property(__short_premiere_date)

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
        _('Images'), null=True, blank=True, help_text='JSON serialized field'
    )

    canonical_image_type_override = models.CharField(
        _('Canonical Image Type Override'),
        max_length=80,
        null=True,
        blank=True,
        help_text='Profile Image Type to use for Canonical Image'
    )

    class Meta:
        abstract = True

    def __get_canonical_image(self):
        if self.images:
            image_list = json.loads(self.images)
            if self.canonical_image_type_override:
                image_type_override = self.canonical_image_type_override
            else:
                image_type_override = None
            return get_canonical_image(
                image_list, image_type_override=image_type_override
            )
        return None

    canonical_image = property(__get_canonical_image)

    def canonical_image_tag(self):
        if self.canonical_image and "http" in self.canonical_image:
            title = (
                f'<a href="{self.canonical_image}" target="_blank">'
                f'{self.canonical_image}</a><br/>'
            )
            img = f'<img src="{self.canonical_image}" width="400">'
            return mark_safe(title + img)
        return None

    canonical_image_tag.short_description = 'Canonical Image (display width=400px)'

    def pretty_image_list(self):
        canonical = self.canonical_image
        if self.images:
            image_list = json.loads(self.images)
            out = '<table width=\"100%\">'
            out += '<tr><th>Profile</th><th>Canonical?</th><th>Updated At</th></tr>'
            for image in image_list:
                out += '\n<tr>'
                out += f'<td><a href="{image["image"]}" target="_new">'
                out += f'{image["profile"]}</a></td>'
                out += f'<td>{str(image["image"] == canonical)}</td>'
                out += f'<td>{image["updated_at"]}</td>'
                out += '</tr>'
            out += '</table>'
            return mark_safe(out)
        return None

    pretty_image_list.short_description = 'Image List'


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
        _('Genre'), null=True, blank=True, help_text='JSON Serialized Field'
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
    language = models.CharField(_('Language'), max_length=10, null=True, blank=True)

    class Meta:
        abstract = True


class PBSMMAudience(models.Model):
    audience = models.TextField(
        _('Audience'), null=True, blank=True, help_text='JSON Serialized Field'
    )

    class Meta:
        abstract = True


class PBSMMHashtag(models.Model):
    hashtag = models.CharField(_('Hashtag'), max_length=100, null=True, blank=True)

    class Meta:
        abstract = True


class PBSMMGenericObject(PBSMMObjectID, PBSMMObjectTitleSortableTitle,
                         PBSMMObjectDescription, PBSMMObjectDates,
                         GenericObjectManagement, PBSObjectMetadata):
    def __get_default_asset(self):
        return get_default_asset(self)

    default_asset = property(__get_default_asset)

    class Meta:
        abstract = True


class PBSMMGenericAsset(PBSMMGenericObject, PBSMMObjectSlug, PBSMMImage, PBSMMFunder,
                        PBSMMPlayerMetadata, PBSMMLinks, PBSMMGeo, PBSMMPlatforms,
                        PBSMMWindows, PBSMMLanguage):
    class Meta:
        abstract = True


class PBSMMGenericRemoteAsset(PBSMMGenericObject):
    class Meta:
        abstract = True


class PBSMMGenericShow(PBSMMGenericObject, GenericAccessControl, PBSMMObjectSlug,
                       PBSMMImage, PBSMMLinks, PBSMMNOLA, PBSMMHashtag, PBSMMGenre,
                       PBSMMFunder, PBSMMPlayerMetadata, PBSMMGoogleTracking,
                       PBSMMEpisodeSeason, PBSMMPlatforms, PBSMMAudience,
                       PBSMMBroadcastDates, PBSMMLanguage):
    class Meta:
        abstract = True


class PBSMMGenericEpisode(
        PBSMMGenericObject,
        GenericAccessControl,
        PBSMMObjectSlug,
        PBSMMFunder,
        PBSMMLanguage,
        PBSMMImage,
        PBSMMBroadcastDates,
        PBSMMNOLA,
        PBSMMLinks,
):
    class Meta:
        abstract = True


class PBSMMGenericSeason(PBSMMGenericObject, GenericAccessControl, PBSMMLinks,
                         PBSMMImage):
    class Meta:
        abstract = True


class PBSMMGenericSpecial(
        PBSMMGenericObject,
        GenericAccessControl,
        PBSMMObjectSlug,
        PBSMMLanguage,
        PBSMMBroadcastDates,
        PBSMMNOLA,
        PBSMMLinks,
):
    class Meta:
        abstract = True


class PBSMMGenericCollection(PBSMMGenericObject, GenericAccessControl, PBSMMObjectSlug,
                             PBSMMImage):
    # There is no sortable title field - it is allowed in the model purely out
    # of laziness since abstracting it out from PBSGenericObject would be
    # more-complicated than leaving it in. PLUS I suspect that eventually it'll
    # be added...
    class Meta:
        abstract = True


class PBSMMGenericFranchise(PBSMMGenericObject, GenericAccessControl, PBSMMObjectSlug,
                            PBSMMFunder, PBSMMNOLA, PBSMMBroadcastDates, PBSMMImage,
                            PBSMMPlatforms, PBSMMLinks, PBSMMHashtag, PBSMMGoogleTracking,
                            PBSMMGenre, PBSMMPlayerMetadata):
    # There is no can_embed_player field - again, laziness (see above)
    class Meta:
        abstract = True
