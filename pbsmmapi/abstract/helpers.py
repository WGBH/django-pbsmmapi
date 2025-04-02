from datetime import datetime

import pytz


def fix_non_aware_datetime(obj):
    """
    Ugh - for SOME REASON some of the DateTime values returned by the PBS MM
    API are NOT time zone aware. SO - fudge them by adding 00:00:00 UTC (if
    even a time is not provided) or assume the time is UTC.
    """
    if obj is None:
        return None
    if ":" not in obj:  # oops no time
        obj += " 00:00:00"
    if "+" not in obj:  # no time zone - use UTC
        if "Z" not in obj:
            obj += "+00:00"
    return obj


def time_zone_aware_now():
    """
    This just sends back a time zone aware "now()" with UTC as the time zone.
    """
    return datetime.now(pytz.utc)
