from ..api.api import get_PBSMM_record
from ..abstract.helpers import set_json_serialized_field
from ..asset.foo import foo

def process_episode_record(obj, instance):
    
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

#### Episode metadata - things related to the episode itself
    instance.nola = attrs.get('nola', None)
    instance.language = attrs.get('language', None)
    instance.funder_message = attrs.get('funder_message', None)
    instance.premiered_on = attrs.get('premiered_on', None)
    instance.encored_on = attrs.get('encored_on', None)
    instance.ordinal = attrs.get('ordinal', None)
    instance.segment = attrs.get('segment', None)

#### Unprocessed - store as JSON fragments
    instance.links = set_json_serialized_field(attrs, 'links', default=None)

#### RELATIONSHIPS
    if instance.ingest_related_assets:
        related_assets_endpoint = links.get('assets', None)
        print "ENDPOINT: ", related_assets_endpoint
        (status, json) = get_PBSMM_record(related_assets_endpoint)
        if status == 200:
            asset_list = json['data']
            print "TYPE ASSET LIST: ", type(asset_list)
            print "LEN: ", len(asset_list)
            for asset in asset_list:
                asset_id = asset.get('id', None)
                print "ASSET ID: ", asset_id
                ingest_related_asset(asset_id)
                #try: 
                #    asset_record = PBSMMAsset.object.get(asset_id = asset_id)
                #except PBSMMAsset.DoesNotExist:
                #    asset_record = PBSMMAsset()
                #    asset_record.asset_id = asset_id
                #asset_record.ingest_on_save = True
                #asset_record.save()
            
                    

    return instance