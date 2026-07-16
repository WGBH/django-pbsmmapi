from datetime import datetime

import pytz


def time_zone_aware_now():
    """
    This just sends back a time zone aware "now()" with UTC as the time zone.
    """
    return datetime.now(pytz.utc)
