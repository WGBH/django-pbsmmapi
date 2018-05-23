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
    # Try 1: get the first one marked "defautl"
    print "OBJ: ", obj
    asset_list = obj.assets.filter(is_default_asset = 1)
    if asset_list:
        return asset_list[0]
    # Oops - try 2 - just get the first one
    asset_list = obj.assets.all()
    if asset_list:
        return asset_list[0]
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
    #print "WITHOUT: ", datetime.now(), "WITH: ", datetime.now(tz=timezone.utc)
    return datetime.now(tz=timezone.utc)