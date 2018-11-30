import json
import pytz
from datetime import datetime

####
# These are helper functions used throughout the package.
####


def set_json_serialized_field(attrs, field, default=None):
    """
    Return a JSON serialized field,
    but don't send back [] or {} or ''
    (return default which default to None)
    """
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
    attempt_one = asset_list.filter(override_default_asset=1)
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


def get_canonical_image(image_list, image_type_override=None):
    """
    Most Objects (except Season for no explicable reason) have an Images JSON serialized field.
    It is a list of images with an associated "profile" value; however, there is no controlled vocabulary
    for this.

    So - if an object has several different images, how do we know which one to use?

        1) Set an image_type_override field.   If this is set, and the type exists in the list,
            then that's the answer.
        2) Look for 'mezzanine' as a sub-string for the image 'profile' value - if you find that,
            return it.
        3) DEFAULT - send back the first image in the list.   That's probably completely random,
            but one needs a backup plan.
        4) (still to be coded) - get the SITE_CANONICAL_IMAGE path from the SETTINGS file:
            This is the absolute last-ditch effort.

    """
    # What's the pattern to look for in the image list 'profile' value
    if image_type_override is None:
        image_type = 'mezzanine'
    else:
        image_type = image_type_override

    # OK - what images are available?
    for img in image_list:
        # Best case scenario - I find the image I'm looking for
        if image_type in img['profile']:
            return img['image']

    if len(image_list) > 0:
        # If I got here then it didn't find the image_type that was requested
        # return the first image in the list
        return image_list[0]['image']
    else:
        # This is my last chance!  Return the SITE_CANONICAL_IMAGE URL from the settings file.
        # I STILL NEED TO CODE THIS
        pass

    return None


def fix_non_aware_datetime(obj):
    """
    Ugh - for SOME REASON some of the DateTime values returned by the PBS MM API are NOT time zone aware.
    SO - fudge them by adding 00:00:00 UTC (if even a time is not provided) or assume the time is UTC.
    """
    if obj is None:
        return None
    if ':' not in obj:  # oops no time
        obj += ' 00:00:00'
    if '+' not in obj:  # no time zone - use UTC
        if 'Z' not in obj:
            obj += '+00:00'
    return obj


def time_zone_aware_now():
    """
    This just sends back a time zone aware "now()" with UTC as the time zone.
    """
    return datetime.now(pytz.utc)


def is_in_the_future(dt):
    """
    Is this (UTC) date/time value in the future or not?
    """
    if dt > datetime.now(pytz.utc):
        return True
    return False
