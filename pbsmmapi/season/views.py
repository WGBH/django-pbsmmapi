from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, TemplateView, ListView

from pbsmmapi.season.models import PBSMMSeason as Season
from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin
from pbsmmapi.abstract.mixin_helpers import filter_offline_shows

class PBSMMSeasonListView(ListView, PBSMMObjectListMixin):
    """
    This is the Season Listing View - it's generic and is Show agnostic.
    Gate-keeping is handled in the PBSMMObjectListMixin class.
    """
    model = Season
    template_name = 'season/season_list.html'
    context_object_name = 'season_list'
    
    def get_queryset(self):
        qs = super(PBSMMSeasonListView, self).get_queryset()
        qs = filter_offline_shows(qs, self.request.user)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMSeasonListView, self).get_context_data(**kwargs)
        return context

        
class PBSMMSeasonDetailView(DetailView, PBSMMObjectDetailMixin):
    """
    This is the Season detail view.
    Gate-keeping is handled in the PBSMMObjectDetailMixin class.
    """
    model = Season
    template_name = 'season/season_detail.html'
    context_object_name = 'season'
    
    def get_object(self, queryset=None):
        obj = super(PBSMMSeasonDetailView, self).get_object(queryset=queryset)
        return obj
        
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMSeasonDetailView, self).get_context_data(**kwargs)
        return context
        