from ..abstract.helpers import set_json_serialized_field

def process_special_record(obj, instance):

# These are the top-level fields - almost everything else is under attrs
    data = obj['data']
    attrs = data['attributes']
    links = obj['links']
    
#### UUID and updated_on
    instance.object_id = data.get('id', None)  # This should always be set.
    instance.updated_at = attrs.get('updated_at', None) # timestamp of the record in the API
    instance.api_endpoint = links.get('self', None) # URL of the request
    
#### Title, Sortable Ttile, and Slug
    instance.title = attrs.get('title', None)
    instance.title_sortable = attrs.get('title_sortable', None)
    instance.slug = attrs.get('slug', None)

#### Descriptions
    instance.description_long = attrs.get('description_long', None)
    instance.description_short = attrs.get('description_short', None)

#### Special metadata - things related to the special itself
    instance.premiered_on = attrs.get('premiered_on', None)
    instance.encored_on = attrs.get('encored_on', None)
    instance.nola = attrs.get('nola', None)
    instance.language = attrs.get('language', None)

#### Unprocessed - store as JSON fragments
    instance.links = set_json_serialized_field(attrs, 'links', default=None)

    return instance