from ..abstract.helpers import set_json_serialized_field, fix_non_aware_datetime


def process_season_record(obj, instance, origin='season'):
    """
    Take the data returned from a single Season's API JSON content and map it to a PBSMMEpisode database record.
    """
    # These are the top-level fields - almost everything else is under attrs
    if 'attributes' not in obj.keys():
        attrs = obj['data']['attributes']
    else:
        attrs = obj['attributes']

    links = obj['links']

    # UUID and updated_on
    if 'id' in obj.keys():
        instance.object_id = obj.get('id', None)  # This should always be set.
    else:
        instance.object_id = obj['data'].get('id')

    instance.updated_at = fix_non_aware_datetime(
        attrs.get('updated_at', None))  # timestamp of the record in the API
    instance.api_endpoint = links.get('self', None)  # URL of the request

    # Title, Sortable Ttile, and Slug
    instance.title = attrs.get('title', None)
    instance.title_sortable = attrs.get('title_sortable', None)

    # Descriptions
    instance.description_long = attrs.get('description_long', None)
    instance.description_short = attrs.get('description_short', None)

    # Season metadata - things related to the season itself
    instance.premiered_on = fix_non_aware_datetime(
        attrs.get('premiered_on', None))
    instance.funder_message = attrs.get('funder_message', None)
    instance.is_excluded_from_dfp = attrs.get('is_excluded_from_dfp', None)
    instance.can_embed_player = attrs.get('can_embed_player', None)
    instance.language = attrs.get('language', None)
    instance.ga_page = attrs.get('tracking_ga_page', None)
    instance.ga_event = attrs.get('tracking_ga_event', None)
    instance.episode_count = attrs.get('episode_count', None)
    instance.display_episode_number = attrs.get('display_episode_number', None)
    instance.sort_episodes_descending = attrs.get(
        'sort_episodes_descending', None)
    instance.ordinal = attrs.get('ordinal', None)
    instance.hashtag = attrs.get('hashtag', None)

    # Unprocessed - store as JSON fragments
    instance.genre = set_json_serialized_field(attrs, 'genre', default=None)
    instance.links = set_json_serialized_field(attrs, 'links', default=None)

    # The canonical image used for this is the one that has 'mezzanine' in it
    instance.images = set_json_serialized_field(attrs, 'images', default=None)
    if instance.images is None:  # try latest_asset_images
        instance.images = set_json_serialized_field(
            attrs, 'latest_asset_images', default=None)

    instance.platforms = set_json_serialized_field(
        attrs, 'platforms', default=None)
    instance.audience = set_json_serialized_field(
        attrs, 'audience', default=None)
        
    # References to parents
    show = attrs.get('show', None)
    instance.show_api_id = show.get('id', None)

    instance.json = obj
    return instance
