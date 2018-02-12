from ..abstract.helpers import set_json_serialized_field

def process_show_record(obj, instance):
    
# These are the top-level fields - almost everything else is under attrs
    data = obj['data']
    attrs = data['attributes']
    links = obj['links']
    
#### UUID and updated_on
    instance.object_id = data.get('id', None)  # This should always be set.
    instance.updated_at = attrs.get('updated_at', None) # timestamp of the record in the API
    instance.link_to_api_record = links.get('self', None) # URL of the request
    
#### Title, Sortable Ttile, and Slug
    instance.title = attrs.get('title', None)
    instance.title_sortable = attrs.get('title_sortable', None)
    instance.slug = attrs.get('slug', None)

#### Descriptions
    instance.description_long = attrs.get('description_long', None)
    instance.description_short = attrs.get('description_short', None)

#### Shoe metadata - things related to the show itself
    instance.premiered_on = attrs.get('premiered_on', None)
    instance.nola = attrs.get('nola', None)
    instance.is_excluded_from_dfp = attrs.get('is_excluded_from_dfp', False) # see the bottom of the file for notes
    instance.can_embed_player = attrs.get('can_embed_player', None)
    instance.language = attrs.get('language', None)
    instance.funder_message = attrs.get('funder_message', None)
    instance.ga_page = attrs.get('tracking_ga_page', None)
    instance.ga_event = attrs.get('tracking_ga_event', None)
    instance.episode_count = attrs.get('episodes_count', None)
    instance.display_episode_number = attrs.get('display_episode_number', False)
    instance.sort_episodes_descending = attrs.get('sort_episodes_descending', False)
    instance.ordinal_season = attrs.get('ordinal_season', True)
    instance.hashtag = attrs.get('hashtag', None)
    
#### Unprocessed - store as JSON fragments
    instance.images = set_json_serialized_field(attrs, 'images', default=None)
    instance.links = set_json_serialized_field(attrs, 'links', default=None)
    instance.platforms = set_json_serialized_field(attrs, 'platforms', default=None)
    instance.genre = set_json_serialized_field(attrs, 'genre', default=None)
    instance.audience = set_json_serialized_field(attrs, 'audience', default=None)
    
    return instance