from datetime import datetime #, tzinfo, timedelta

import dateutil.parser
import json
from django.utils import timezone

### This is to set up timezone-aware timestamps.   
###  The PBSMM API stores dates in UTC as strings that are ISO-8601/RFC-3339 compliant
#ZERO = timedelta(0)
#
#class UTC(tzinfo):
#  def utcoffset(self, dt):
#    return ZERO
#  def tzname(self, dt):
#    return "UTC"
#  def dst(self, dt):
#    return ZERO
#
#utc = UTC()

def check_asset_availability(start=None, end=None):
    now = datetime.now(tz=timezone.utc)
    
    if start:
        start_date = dateutil.parser.parse(start)
    if end:
        end_date = dateutil.parser.parse(end)
    
    if start and now < start_date:
        return (False, 0, 'not-yet-available')
    else:
        if end is None or now <= end_date:
            return (True, 1, 'available')
        if end and now > end_date:
            return (False, 2, 'expired')
            
    return (False, -1, 'unknown')
    
