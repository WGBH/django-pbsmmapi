import pytz
from datetime import datetime

from django.db.models import Q
from django.http import Http404
from django.views.generic.base import ContextMixin
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.list import MultipleObjectMixin

from .gatekeeper import can_object_page_be_shown

"""
These are the View mixins for PBSMM objects.

They apply the gatekeeper rules.

See the documentation in gatekeeper.py for details.
"""


class GenericAuthenticationMixin(ContextMixin):
    """
    These are done for all the Listing and Detail pages...

    Aren't mixins just freaking cool?
    """

    def get_context_data(self, **kwargs):
        context = super(
            GenericAuthenticationMixin,
            self).get_context_data(
            **kwargs)
        context['is_logged_in'] = self.request.user.is_authenticated
        return context


class PBSMMObjectListMixin(MultipleObjectMixin, GenericAuthenticationMixin):
    """
    This is for Listing views that apply to all object ListView classes.

    This handles self-filtering.  Some object types ALSO require ancestral "back filtering"
        (e.g., Episodes must have a Season that is available;  Specials and S(easons require
        their Show is available, etc.).   Those filters are applied AFTER these, and are
        called from the specific ListView class.
    """

    def get_queryset(self):
        qs = super(PBSMMObjectListMixin, self).get_queryset()

        # No one can see objects with publish_status < 0
        qs = qs.exclude(publish_status__lt=0)

        # If you're logged in you can see everything else.
        user = self.request.user
        if not user.is_authenticated:
            # If you are not logged in, then live_as_of must exist (not None)
            # and must be in the past.
            condition_1 = Q(publish_status=0)
            condition_2 = Q(live_as_of__gt=datetime.now(pytz.utc))
            condition_3 = Q(live_as_of__isnull=True)
            qs = qs.exclude(condition_1 & condition_2)
            qs = qs.exclude(condition_1 & condition_3)
        return qs


class PBSMMObjectDetailMixin(SingleObjectMixin, GenericAuthenticationMixin):
    """
    This is for detail views that apply to all object DetailView classes.

    This handles self-filtering.  Some object types ALSO require ancestral "back filtering"
    (e.g., an Episode must have an availble Season; a Special must have an available Show).
    Those additional filters are applied AFTER these, and are called from the special DetailView class.
    """

    def get_object(self, queryset=None):
        obj = super(PBSMMObjectDetailMixin, self).get_object(queryset=queryset)
        user = self.request.user
        if can_object_page_be_shown(user, obj):
            return obj
        else:
            raise Http404()
