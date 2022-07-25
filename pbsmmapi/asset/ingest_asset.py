from http import HTTPStatus
from pbsmmapi.abstract.helpers import fix_non_aware_datetime
from pbsmmapi.api.api import get_PBSMM_record


# This is the code that parses the JSON for an Asset returned by the PBSMM API, and
# puts it into the schema for an *-Asset object (e.g., EpisodeAsset, ShowAsset, etc.;
# all *-Asset models have the same structure, only the FK to the parent changes).
#
# This is USUALLY called when ingesting a ancestral object, i.e.:
#     After an ancestral object is ingested from the API (e.g., an Episode),
#     all of the associated Assets are ingested (with the code below).

# THIS IS THE INGEST SCRIPT FOR ASSET RECORDS
PBSMM_ASSET_ENDPOINT = 'https://media.services.pbs.org/api/v1/assets/'

def process_asset_record(obj, instance, origin=None):
    # Here is where all the scraping of the Asset record is done
    #
    # These are the top-level fields - almost everything else is under attrs
    # attrs = obj['attributes']
    # links = obj['links']

    url = "{}{}/".format(PBSMM_ASSET_ENDPOINT, obj.get('id'))

    (status, json) = get_PBSMM_record(url)

    #should we abort at this time or just go with some data= better than no data?
    if status != HTTPStatus.OK:
        json = obj

    if 'attributes' in json.keys():
        attrs = json.get('attributes')
    else:
        if 'data' in json.keys():
            attrs = json['data'].get('attributes')

    links = obj.get('links')

    # UUID and updated_on
    # we want this because sometimes we've looked it up via COVE ID, not
    # knowing the UUID
    instance.object_id = obj.get('id', None)

    instance.updated_at = fix_non_aware_datetime(
        attrs.get('updated_at', None)
    )  # timestamp of the record in the API
    instance.api_endpoint = links.get('self', None)  # the URL of the request

    # Title, Sortable Title, and Slug
    instance.title = attrs.get('title', None)
    instance.title_sortable = attrs.get('title_sortable', None)
    instance.slug = attrs.get('slug', None)
    instance.legacy_tp_media_id = attrs.get('legacy_tp_media_id', None)

    # Descriptions
    instance.description_long = attrs.get('description_long', None)
    instance.description_short = attrs.get('description_short', None)

    # Asset metadata - things related to the asset itself
    instance.is_excluded_from_dfp = attrs.get(
        'is_excluded_from_dfp', False
    )  # see the bottom of the file for notes
    # this is the <iframe> to show the asset
    instance.player_code = attrs.get('player_code', None)
    instance.can_embed_player = attrs.get('can_embed_player', None)
    instance.duration = attrs.get('duration', None)  # in seconds
    # 'clip', 'full-length', or 'preview'
    instance.object_type = attrs.get('object_type', None)
    instance.language = attrs.get('language', None)

    # Unprocessed
    instance.tags = attrs.get('tags', None)
    # Availabilty is in three parts: public, station_members, local_members -
    # there might be different dates for each
    instance.availability = attrs.get('availabilities', None)
    # The canonical image used for this is the one that has 'mezzanine' in it
    instance.images = attrs.get('images', None)
    # This can have things like "where to buy the DVD" for shows - not too
    # useful (so far) for Asset records
    instance.links = attrs.get('links', None)
    # Basically, this is the set of places one is allowed to access the asset
    instance.geo_profile = attrs.get('geo_profile', None)
    # For compatibility (so far)
    instance.platforms = attrs.get('platforms', None)

    instance.json = json

    return instance
