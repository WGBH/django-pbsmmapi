from ..abstract.helpers import set_json_serialized_field

### THIS IS THE INGEST SCRIPT FOR ASSET RECORDS

# This just makes nice serialized JSON content fragments from the API record's JSON content.
# It's a dirty way to avoid having to create ancillary tables with foreign keys back to objects.
# For example, let's say there's a field that shows all of the available languages for an object; do you
# REALLY want to have N records for EACH object that just says object #1234 is in English/Spanish?
# No - of course you don't.   So instead have a SINGLE simple field that has the value of, e.g., 
# ['en', 'es'] that you can de-serialize as necessary with the appropriate tests.
#
# I find that this works GREAT with model properties.  Using the above example you could quickly create
# a "is_spanish_available" property in a few lines:
#
#    def is_spanish_available(self):
#        langs = json.loads(self.languages)
#        return 'en' in lange
#    is_spanish_available = property(is_spanish_available)
#
# Wow - that was simple!
# RAD - 6 Feb 2018

def process_asset_record(obj, instance):
# Here is where all the scraping of the Asset record is done
#
# These are the top-level fields - almost everything else is under attrs
    data = obj['data']
    attrs = data['attributes']
    links = obj['links']
    
#### UUID and updated_on
    instance.object_id = data.get('id', None) # we want this because sometimes we've looked it up via COVE ID, not knowing the UUID
    instance.updated_at = attrs.get('updated_at', None)  # timestamp of the record in the API
    instance.link_to_api_record = links.get('self', None) # the URL of the request

#### Title, Sortable Title, and Slug
    instance.title = attrs.get('title', None)
    instance.title_sortable = attrs.get('title_sortable', None)
    instance.slug = attrs.get('slug', None)
    instance.legacy_tp_media_id = attrs.get('legacy_tp_media_id', None)
    
#### Descriptions
    instance.description_long = attrs.get('description_long', None)
    instance.description_short = attrs.get('description_short', None)
    
#### Asset metadata - things related to the asset itself
    instance.is_excluded_from_dfp = attrs.get('is_excluded_from_dfp', False) # see the bottom of the file for notes
    instance.player_code = attrs.get('player_code', None) # this is the <iframe> to show the asset
    instance.can_embed_player = attrs.get('can_embed_player', None)
    instance.duration = attrs.get('duration', None) # in seconds
    instance.object_type = attrs.get('object_type', None) # 'clip', 'full-length', or 'preview'
    instance.content_rating = attrs.get('content_rating', None) # e.g., 'TV-G'
    instance.content_rating_description = attrs.get('content_rating_description', None)
    instance.language = attrs.get('language', None)
    
#### Unprocessed
    instance.tags = set_json_serialized_field(attrs, 'tags', default=None)
    # According to PBS this isn't really used - legacy for some third parties - skipping
    # However, Antiques Roadshow appears to be one of them.
    instance.topics = set_json_serialized_field(attrs, 'topics', default=None)
    # Availabilty is in three parts: public, station_members, local_members - there might be different dates for each
    instance.availability = set_json_serialized_field(attrs, 'availabilities', default=None)
    # The canonical image used for this is the one that has 'mezzanine' in it
    instance.images = set_json_serialized_field(attrs, 'images', default=None)
    # This can have things like "where to buy the DVD" for shows - not too useful (so far) for Asset records
    instance.links = set_json_serialized_field(attrs, 'links', default=None)
    # Basically, this is the set of places one is allowed to access the asset
    instance.geo_profile = set_json_serialized_field(attrs, 'geo_profile', default=None)
    # For compatibility (so far)
    instance.platforms = set_json_serialized_field(attrs, 'platforms', default=None)
    
#### Relationships

    # RELATED LINKS
    # RELATED PROMOS
    
    # Episode
    # Season
    # Show
    # Franchise
    
    
    return instance

##### DFP?
# It appears to be a signal for DFP Sponsorship - which from what I understand has something to do with Google Videos
# and I think somehow this is a way to get around viewers seeing third-party ads on those assets.
# In any case, I've included the field for completeness.   RAD 6-Feb-2018
    
#####
# I'm putting this here because I know it'll be extremely useful for hiding corpses.
#
# import json
# x = [1,2,3,4,5]   # create a list
# jx = json.dumps(x) # turn it into a string rep
# jx 
# >>> '[1, 2, 3, 4, 5]'   # oh look it's a string
# jq = json.loads(jx)   # convert the string back into a list
# jq
# >>>>> [1, 2, 3, 4, 5] # oh look it's a list
#
# This works for dict too...

