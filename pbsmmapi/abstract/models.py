# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.utils.translation import ugettext_lazy as _
from django.db import models

######################### LOCAL ABSTRACT MODELS ############################
#
# These are internal to this app - not part of the API - for record management
#
class GenericObjectManagement(models.Model):
    date_created = models.DateTimeField (
        _('Created On'),
        auto_now_add = True,
        help_text = "Not set by API",
    )
    date_last_api_update = models.DateTimeField (
        _('Last API Retrieval'),
        help_text = "Not set by API",
        null = True
    )
    ingest_on_save = models.BooleanField (
        _('Ingest on Save'),
        default = False,
        help_text = 'If true, then will update values from the PBSMM API on save()'
    )
    last_api_status = models.PositiveIntegerField (
        _('Last API Status'),
        null = True, blank = True
    )

    class Meta:
        abstract = True
        
    def last_api_status_color(self):
        template = '<b><span style="color:#%s;">%d</span></b>'
        if self.last_api_status:
            if self.last_api_status == 200:
                return template % ('0f0', self.last_api_status)
            else:
                return template % ('f00', self.last_api_status)
        return self.last_api_status
    last_api_status_color.allow_tags = True
    last_api_status_color.short_description = 'Status'


######################### ABSTRACT MODELS FROM PBSMM FIELDS ##################################
class PBSMMObjectID(models.Model):
#
# In most parallel universes, we'd use this as the PRIMARY KEY.
# However, given the periodic necessity of having to EDIT records or manipulate them in the database, the
# issue of having to juggle 32-length random characters instead of a nice integer ID would be a PITA.
#
# So I'm being "un-pure".  Sue me.   RAD 31-Jan-2018
#
    object_id = models.UUIDField (
        _('Object ID'),
        unique = True,
        null = True, blank = True # does this work?
    )
    
    class Meta:
        abstract = True
        
class PBSObjectMetadata(models.Model):
# Exists for all objects
    link_to_api_record = models.URLField (
        _('Link to API Record'),
        null = True, blank = True,
        help_text = 'Endpoint to original record from the API'
    )
    #
    # This just makes the field clickable in the Admin (why cut and paste when you can click?)
    def link_to_api_record_link(self):
        return '<a href="%s" target="_new">%s</a>' % (self.link_to_api_record, self.link_to_api_record)
    link_to_api_record_link.allow_tags = True
    link_to_api_record_link.short_description = 'Link to API'
    
    class Meta:
        abstract = True
        
class PBSMMObjectTitle(models.Model):
# Exists for all objects
    title = models.CharField (
        _('Title'),
        max_length = 200,
        null = True, blank = True
    )
    class Meta:
        abstract = True
        
class PBSMMObjectSortableTitle(models.Model):
# Exists for all objects EXCEPT Collection - so we have to separate it 
# (I don't understand why the API just didn't create this across records...)    
    title_sortable = models.CharField (
        _('Sortable Title'),
        max_length = 200,
        null = True, blank = True
    )
    class Meta:
        abstract = True
        
class PBSMMObjectSlug(models.Model):
# These exist for all objects EXCEPT Season
# (see note/whine on PBSMMObjectSortableTitle)
    slug = models.SlugField (
        _('Slug'),
        unique = True,
        max_length = 200,
    )
    
    class Meta:
        abstract = True
        
class PBSMMObjectTitleSortableTitle(PBSMMObjectTitle, PBSMMObjectSortableTitle):
# Lump them together
    class Meta:
        abstract = True


#############################
############################# FIELDS DEFINITELY ASSOCIATED WITH ALL OBJECTS (confirmed)
#############################
class PBSMMObjectDescription(models.Model):
# These exist for all Objects
    description_long = models.TextField (
        _('Long Description')
    )
    description_short = models.TextField (
        _('Short Description')
    )
    
    class Meta:
        abstract = True
        
class PBSMMObjectDates(models.Model):
# This exists for all objects
    updated_at = models.DateTimeField (
        _('Updated At'),
        null = True, blank = True,
        help_text = 'API record modified date'
    )
    
    class Meta:
        abstract = True
        
#############################
############################# FIELDS DEFINITELY ASSOCIATED WITH SOME BUT NOT ALL OBJECTS (confirmed)
#############################

###############
########## FIELDS ASSOCIATED WITH BROADCAST OR PREMIERE (on whatever platform)
###############
class PBSMMBroadcastDates(models.Model):
# TO BE CONFIRMED
# premiered_on exists for Episode, Franchise, Show, and Special but NOT Collection or Season
# encored_on ONLY exists for Episode
# so we might have to split them up
    premiered_on = models.DateTimeField (
        _('Premiered On'),
        null = True, blank = True
    )
    #encored_on = models.DateTimeField (
    #    _('Encored On'),
    #    null = True, blank = True
    #)
    
    class Meta:
        abstract = True
        
class PBSMMNOLA(models.Model):
# This exists for Episode, Franchise, and Special but NOT for Collection, Show, or Season
    nola = models.CharField (
        _('NOLA Code'),
        max_length = 8,
        null = True, blank = True
    )

    class Meta:
        abstract = True

# Here's something annoying
# images only exists for Asset, but the other object have images, just called something else.
# I have to decide whether I will abide by this nomenclature or not
class PBSMMImage(models.Model):
    images = models.TextField (
        _('Images'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )
    
    class Meta:
        abstract = True
        
class PBSMMFunder(models.Model):
    funder_message = models.TextField (
        _('Funder Message'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )
    
    class Meta:
        abstract = True

class PBSMMPlayerMetadata(models.Model):
    is_excluded_from_dfp = models.BooleanField (
        _('Is excluded from DFP'),
        default = False
    )
    
    can_embed_player = models.BooleanField (
        _('Can Embed Player'),
        default = False
    )
    
    class Meta:
        abstract = True

class PBSMMLinks(models.Model):
    links = models.TextField (
        _('Links'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )
    
    class Meta:
        abstract = True
        
class PBSMMPlatforms(models.Model):
    platforms = models.TextField (
        _('Platforms'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )
    
    class Meta:
        abstract = True
        

class PBSMMWindows(models.Model):
    windows = models.TextField (
        _('Windows'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )

    class Meta:
        abstract = True
        
class PBSMMGeo(models.Model):
    # countries --- hold off until needed
    geo_profile = models.TextField (
        _('Geo Profile'),
        null = True, blank = True,
        help_text = 'JSON serialized field'
    )
    
    class Meta:
        abstract = True
        
class PBSMMGoogleTracking(models.Model):
    ga_page = models.CharField (
        _('GA Page Tag'),
        max_length = 40,
        null = True, blank = True
    )
    ga_event = models.CharField (
        _('GA Event Tag'),
        max_length = 40,
        null = True, blank = True
    )
    
    class Meta:
        abstract = True
        
class PBSMMGenre(models.Model):
    genre = models.TextField (
        _('Genre'),
        null = True, blank = True,
        help_text = 'JSON Serialized Field'
    )
    
    class Meta:
        abstract = True

class PBSMMEpisodeSeason(models.Model):
    episode_count = models.PositiveIntegerField (
        _('Episode Count'),
        null = True, blank = True
    )
    display_episode_number = models.BooleanField (
        _('Display Episode Number'),
        default = False
    )
    sort_episodes_descending = models.BooleanField (
        _('Sort Episodes Descending'),
        default = False
    )
    ordinal_season = models.BooleanField (
        _('Ordinal Season'),
        default = True
    )
    
    class Meta:
        abstract = True
        
class PBSMMLanguage(models.Model):
    language = models.CharField (
        _('Language'),
        max_length = 10,
        null = True, blank = True
    )
    
    class Meta:
        abstract = True
        
class PBSMMAudience(models.Model):
    audience = models.TextField (
        _('Audience'),
        null = True, blank = True,
        help_text = 'JSON Serialized Field'
    )
    
    class Meta:
        abstract = True
        
class PBSMMHashtag(models.Model):
    hashtag = models.CharField (
        _('Hashtag'),
        max_length = 100,
        null = True, blank = True
    )
    
    class Meta:
        abstract = True

### OTHER FIELDS THAT I NEED TO ASSIGN
#
# is_excluded_from_dfp (Boolean) --- Asset, Franchise, Show, Special
# type (CV) --- this is a string that identifies the object type - it can be a property
# can_embed_player (Boolean) --- Asset, Show, Special,  but NOT Collection, Franchise, Episode, or Season  (TO BE CONFIRMED)
# language (CV) --- Asset, Episode, Show, Special, but NOT Collection, Franchise, or Season (TO BE CONFIRMED)
# funder_message (Text) --- Asset, Franchise, Show, Special but NOT Collection, Episode, or Season (TO BE CONFIRMED)
# images [list] --- Asset, Franchise, Show, Special but NOT Collection, Episode, or Season (TO BE CONFIRMED)
# featured (Boolean) --- ONLY Collection (TO BE CONFIRMED)
# nola (Char) --- Episode, Franchise, and Special, but NOT Asset, Episode, Show, or Season
# platforms [list] --- Asset, Franchise, Show, and Special, but NOT Collection, Episode, or Season
# audiences [list] --- Show and Special but NOT Asset, Collection, Episode, or Franchise
# links [list] --- Episode, Franchise, Season, Show, and Special but NOT Asset or Collection
#
# These appear to only apply to Franchise, Show and Special
#
# genre (CV) --- Franchise, Show, and Specual but NOT Asset, Collection, Episode, or Season
# tracking_ga_page (Char) --- Franchise, Show, Special but NOT Asset, Collection, Episode, or Season
# tracking_ga_eent (Char) --- Franchise, Show, Special but NOT Asset, Collection, Episode, or Season
# hashtag (Char) --- Franchise, Show, Special but NOT Asset, Collection, Episode, or Season
# 
# These appear to only apply to Show and Speciak
# display_episode_number (Boolean) - this distinguishes between episodes that have a title vs. those that ref with e.g., "Episode 4"
# ordinal_season (Boolean) - similar: "Season 4"
# episode_count (Integer) - I guess to do "Episode 4 of 5"

#
# FOREIGN KEYS - these objects can be embedded within other Objects
#
# Franchise - can appear within Asset, Show, and Special
# Season - can appear within Asset, and Episode
# Show - can appear within Asset, Collection, Show, and Season
# Episode - can appear within Asset and Collection
# Special - can appear within Collection
#

######################### META ABSTRACT MODELS ############################# - common to almost EVERY object type
class PBSMMGenericObject(
        PBSMMObjectID, 
        PBSMMObjectTitleSortableTitle, 
        PBSMMObjectDescription, 
        PBSMMObjectDates, 
        GenericObjectManagement,
        PBSObjectMetadata
    ):
    
    class Meta:
        abstract = True
        
class PBSMMGenericAsset(PBSMMGenericObject, PBSMMObjectSlug,
            PBSMMImage, PBSMMFunder, PBSMMPlayerMetadata, PBSMMLinks, PBSMMGeo, 
            PBSMMPlatforms, PBSMMWindows, PBSMMLanguage
        ):
        
    class Meta:
        abstract = True
        
class PBSMMGenericRemoteAsset(PBSMMGenericObject):

    class Meta:
        abstract = True
        
class PBSMMGenericShow(PBSMMGenericObject, PBSMMObjectSlug,
            PBSMMImage, PBSMMLinks, PBSMMNOLA, PBSMMHashtag,
            PBSMMGenre, PBSMMFunder, PBSMMPlayerMetadata,
            PBSMMGoogleTracking, PBSMMEpisodeSeason,
            PBSMMPlatforms, PBSMMAudience, PBSMMBroadcastDates,
            PBSMMLanguage,
        ):
        
    class Meta:
        abstract = True
        
class PBSMMGenericEpisode(PBSMMGenericObject, PBSMMObjectSlug,
            PBSMMFunder, PBSMMLanguage,
            PBSMMBroadcastDates, PBSMMNOLA, PBSMMLinks,
        ):
        
    class Meta:
        abstract = True
    
class PBSMMGenericSeason(PBSMMGenericObject, PBSMMLinks, PBSMMImage):
    class Meta:
        abstract = True
        
class PBSMMGenericSpecial(PBSMMGenericObject, PBSMMObjectSlug,
            #PBSMMPlayerMetadata,
            #PBSMMFunder, 
            PBSMMLanguage,
            #PBSMMImage, 
            PBSMMLinks,
            #PBSMMPlatforms, PBSMMAudience, 
            PBSMMBroadcastDates,
            #PBSMMGenre, PBSMMGoogleTracking, PBSMMHashtag,
            #PBSMMEpisodeSeason
            PBSMMNOLA,
        ):
        
    class Meta:
        abstract = True