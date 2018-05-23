import json
from django.utils import timezone
from datetime import datetime

def set_json_serialized_field(attrs, field, default=None):
# Return a JSON serialized field, 
# but don't send back [] or {} or '' 
# (return default which default to None)
    val = attrs.get(field, default)
    if val:
        return json.dumps(val)
    else:
        return default
        
def get_default_asset(obj):
    """
    Some objects have >1 assets associated with them.
    One common example is that an episode might have a Preview long before
    the episode airs, then will have a full-length video for some time,
    which might expire, after which we'll want the Preview again.
    
    There is NOTHING in the PBSMM API that tells you WHICH Asset associated
    with an object is the "most appropriate one".   Therefore we need a function
    to guess.
    
    Each Asset model has a "is_default_asset" flag which can be set by the content
    producer.  This is taken as the canonical answer.   Failing that, this will 
    return  a) the first available "full length" asset it encounters, or 
    b) the first available asset.   If nothing is available, it will return nothing.
    """
    asset_list = obj.assets.all()
    # Try 1: get the first one marked "defautl"
    attempt_one = asset_list.filter(override_default_asset = 1)
    if attempt_one:
        for x in attempt_one:
            if x.is_asset_publicly_available():
                return x
    # Try 2: get the first one marked "full length"
    attempt_two = asset_list.filter(object_type='full_length')
    if attempt_two:
        for x in attempt_two:
            if x.is_asset_publicly_available():
                return x
    # Try 3: get the first asset on the list
    if asset_list:
        for x in asset_list:
            if x.is_asset_publicly_available():
                return x
    # NO ASSET FOR YOU!
    return None
        
def get_canonical_image(image_list, image_type_override = None):
    if image_type_override is None:
        image_type = 'mezzanine'
    else:
        image_type = image_type_override
        
    for img in image_list:
        if image_type in img['profile']:
            return img['image']
    # If I got here then it didn't find the image_type that was requested
    # return the first image in the list
    if len(image_list) > 0:
        return image_list[0]['image']
    return None
    
def fix_non_aware_datetime(obj):
    if obj is None:
        return None
    if ':' not in obj:  # oops no time
        obj += ' 00:00:00'
    if '+' not in obj:  # no time zone - use UTC
        if 'Z' not in obj:
            obj += '+00:00'
    return obj
    
def non_aware_now():
    return datetime.now(tz=timezone.utc)