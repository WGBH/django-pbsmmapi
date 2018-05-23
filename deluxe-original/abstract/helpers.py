import json

def set_json_serialized_field(attrs, field, default=None):
# Return a JSON serialized field, but don't send back [] or {} or '' (return default which default to None)
    val = attrs.get(field, default)
    if val:
        return json.dumps(val)
    else:
        return default
        
def get_canonical_image(image_list, image_type='mezzanine'):
    for img in image_list:
        if image_type in img['profile']:
            return img['image']
    return None
    