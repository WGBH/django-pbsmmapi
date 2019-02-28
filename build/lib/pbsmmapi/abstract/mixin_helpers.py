import pytz
from datetime import datetime
from django.db.models import Q
from django.http import Http404
from .gatekeeper import can_object_page_be_shown
"""
These functions are extensions of the generic PBSMMObject mixins.

Their purpose is to having "backwards filtering" of lists of objects in the gatekeeper
in case the object's PARENT isn't available as requested.

So - this means, e.g.:
    1. A Special whose parent Show isn't available is LIKEWISE not available EVEN IF
        the object's settings say otherwise.
    2. An Episode whose parent Season isn't available (or that Season's Show) is LIKEWISE not
        available EVEN IF the object's settings say otherwise.

This (so far) does NOT apply to Detail pages, only listing pages.
Why?  Because there might be a very fringe case where you have an Episode/Special whose detail
page you DO want available but out of context of the overall framework.

In this situation, you COULD link directly to the affected page from elsewhere and it would appear,
even though it would not appear on the object's listing page.

"""
##########################################################################
# ListView filters
##########################################################################


# Used to filter out seasons and specials whose Shows are not available
def filter_offline_shows(queryset, is_logged_in):
    """
    This is used by the PBSMMSpecialListView and PBSMMSeasonListView to self-filter objects whose
    parents are not online.
    (Unless you're logged into the Admin.)
    """
    # Rule 1: exclude any publish_status < 0  (for all cases)
    queryset = queryset.exclude(show__publish_status__lt=0)

    # Non-Admin users may only see objects with publish_status == 0 whose
    # live_as_of date exists and is in the past
    if not is_logged_in:
        now = datetime.now(pytz.utc)
        condition_1 = Q(show__publish_status=0)
        condition_2 = Q(show__live_as_of__isnull=True)
        condition_3 = Q(show__live_as_of__gt=now)
        queryset = queryset.exclude(condition_1 & condition_2)
        queryset = queryset.exclude(condition_1 & condition_3)
    # Otherwise it's available
    return queryset


# Used to filter out episodes whose seasons are not available
def filter_offline_seasons(queryset, is_logged_in):
    """
    This is used by the PBSMMEpisodeListView to self-filter objects whose parents are not online.
    (Unless you're logged into the Admin)
    """
    # Rule 1: both my parental Season and my grand-parental Show may not have
    # publish_status < 0
    queryset = queryset.exclude(season__publish_status__lt=0)
    queryset = queryset.exclude(season__show__publish_status__lt=0)

    # If you're logged in then all remaining objects are available to you at this point.
    # Otherwise there are still two other cases to check;  you're parental Season and grand-parental Show
    # must be available to you.
    if not is_logged_in:
        now = datetime.now(pytz.utc)

        # Rule 2 - my parental Season must be available to me
        condition_1 = Q(season__publish_status=0)
        condition_2 = Q(season__live_as_of__isnull=True)
        condition_3 = Q(season__live_as_of__gt=now)
        queryset = queryset.exclude(condition_1 & condition_2)
        queryset = queryset.exclude(condition_1 & condition_3)

        # Rule 3 - my grand-parental Show much be available to me
        condition_4 = Q(season__show__publish_status=0)
        condition_5 = Q(season__show__live_as_of__isnull=True)
        condition_6 = Q(season__show__live_as_of__gt=now)
        queryset = queryset.exclude(condition_4 & condition_5)
        queryset = queryset.exclude(condition_4 & condition_6)

    return queryset

##########################################################################
# DetailView filters
##########################################################################


# Used to filter out seasons and specials whose Shows are not available
def filter_offline_parent_show(obj, user):
    """
    This is for Specials and Seasons - if my Show is not available, than I am likewise not available.
    Remember that "Available" also depends on whether you are logged into the Admin.
    """
    if can_object_page_be_shown(user, obj.show):
        return obj
    raise Http404()


# Used to filter out episodes whose seasons are not available
def filter_offline_parent_season(obj, user):
    """
    This is for Episodes - if my Season or my Season's Show are not available, then I am likewise not available.
    Remember that "Available" also depends on whether you are logged into the Admin.
    """
    if can_object_page_be_shown(user, obj.season):
        if can_object_page_be_shown(user, obj.season.show):
            return obj
    raise Http404()
