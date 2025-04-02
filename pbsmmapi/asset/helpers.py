from datetime import datetime

from dateutil import parser
import pytz


def check_asset_availability(start=None, end=None):
    """
    Am I within the Asset's availablity window?

    If "start" is defined,  now >= start must be True
    If "end" is defined, now <= end must be True.

    Otherwise each condition is presumed TRUE
        (e.g., no "end" date means that it doesn't expire, hence "True")

    Returns a 3-ple:
        0: True or False
        1: A code  -1 = unknown, 0 = not-yet-available, 1 = available, 2 = expired
        2: the text associated with the code (see previous line)
    """
    now = datetime.now(pytz.utc)

    if start:
        start_date = parser.parse(start)
    if end:
        end_date = parser.parse(end)

    if start and now < start_date:
        return (False, 0, "not-yet-available")
    if end is None or now <= end_date:
        return (True, 1, "available")
    if end and now > end_date:
        return (False, 2, "expired")

    return (False, -1, "unknown")
