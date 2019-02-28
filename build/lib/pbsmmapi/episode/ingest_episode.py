from ..abstract.helpers import set_json_serialized_field, fix_non_aware_datetime


def process_episode_record(obj, instance):
    """
    This is the code that takes a PBSMM API-returned Episode and aligns it with a PBSMMEpisode database record.
    """
    # These are the top-level fields - almost everything else is under attrs
    if 'attributes' not in obj.keys():
        attrs = obj['data'].get('attributes')
    else:
        attrs = obj['attributes']

    links = obj['links']

    # UUID and updated_on
    if 'id' not in obj.keys():
        instance.object_id = obj['data'].get('id')
    else:
        instance.object_id = obj.get('id', None)  # This should always be set.

    instance.updated_at = fix_non_aware_datetime(
        attrs.get('updated_at', None))  # timestamp of the record in the API
    instance.api_endpoint = links.get('self', None)  # URL of the request

    # Title, Sortable Ttile, and Slug
    instance.title = attrs.get('title', None)
    instance.title_sortable = attrs.get('title_sortable', None)
    instance.slug = attrs.get('slug', None)

    # Descriptions
    instance.description_long = attrs.get('description_long', None)
    instance.description_short = attrs.get('description_short', None)

    # Episode metadata - things related to the episode itself
    instance.nola = attrs.get('nola', None)
    instance.language = attrs.get('language', None)
    instance.funder_message = attrs.get('funder_message', None)
    instance.premiered_on = fix_non_aware_datetime(
        attrs.get('premiered_on', None))
    instance.encored_on = fix_non_aware_datetime(attrs.get('encored_on', None))
    instance.ordinal = attrs.get('ordinal', None)
    instance.segment = attrs.get('segment', None)

    # Unprocessed - store as JSON fragments
    instance.links = set_json_serialized_field(attrs, 'links', default=None)

    instance.json = obj
    return instance
