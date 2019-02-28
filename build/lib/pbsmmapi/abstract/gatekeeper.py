from datetime import datetime
import pytz

"""
 THIS IS THE MAIN GATEKEEPER

 This controls WHICH records show up on a website, based upon a set of rules.

 It returns True or False given:
    1. the requests.user object (which can be None)
    2. one of the PBSMM objects (Episode, Season, Site, Special)

 How this works:

    There are five possible publish states an object can be in.
        1. (publish_status =  1): Object is PERMANANTLY LIVE - think of this as a ALWAYS ON switch
        2. (publish_status =  0): Object is CONDITIONALLY LIVE - the "live_as_of" date is in the past
        3. (publish_status =  0): Object is PENDING LIVE - the "live_as_of" date is still in the future
        4. (publish_status =  0): Object is NOT YET PUBLISHED - the "live_as_of" date is NULL
        4. (publish_status = -1): Object is PERMANENYLU OFFLINE - this is the ALWAYS OFF Switch

 Page requesters can either be logged in to the Django Admin (i.e., staff) or not (i.e., the general public)

    RULE 1:   Objects - when created start off with publish_status = 0 and live_as_of = None
        This means that the logged-in Admin user can edit the record and "see" the page for Q/A,
            but it is NOT AVAILABLE to the public.

    RULL 2:   Objects only appear to the public (i.e., 'are live') if:
        a. The publish_status = 1 regardless of the live_as_of date
        b. The publish_status = 0 AND the live_as_of date exists and is in the past.

    RULE 3:   Objects with a publish_status of -1 don't appear on the site to anyone.

    RULL 4:   Objects are shown on listing pages to the public ONLY IF:
        a.  The obkect is "live" (see Rule 2)
        b.  Any PARENT objects ARE ALSO "live"
"""


def can_object_page_be_shown(user, this_object):
    try:
        if user.is_staff:  # admin users can always see pages
            if this_object.publish_status >= 0:
                return True  # I can see everything except specifically turned-off objects because I'm an admin
            else:
                return False  # This object is turned off.
    except BaseException:
        pass  # I am not logged in - continue

    if not this_object:  # this object isn't live or doesn't exist
        return False
    if this_object.publish_status < 0:  # this object isn't live
        return False
    if this_object.publish_status == 1:  # this object is live
        return True
    if this_object.publish_status == 0:  # this object MIGHT be live

        if this_object.live_as_of is not None:
            now = datetime.now(pytz.utc)
            # if I'm past my publish date it's LIVE, otherwise it's not live
            # yet
            return this_object.live_as_of <= now
        else:
            # this object is still being working on - no publish date set yet.
            return False
    return True

# TEST CODE FROM SHELL
#from pbsmmapi.abstract.gatekeeper import can_object_page_be_shown
#from pbsmmapi.show.models import PBSMMShow
#ss = PBSMMShow.objects.all()
#from django.contrib.auth.models import User
#user = User.objects.first()
#import pytz
#from datetime import datetime
#future = datetime(2018, 9, 1, 0, 0, 0, 0, pytz.utc)
#past = datetime(2018, 5, 1, 0, 0, 0, 0, pytz.utc)
#now = datetime.now(pytz.utc)

# for s in ss:
#    s.live_as_of = past

#ss[10].live_as_of = None
#ss[11].live_as_of = future
#ss[7].publish_status = 1
#ss[6].publish_status = -1

# for s in ss:
#   can_object_page_be_shown(None, s)
#   can_object_page_be_shown(user, s)
