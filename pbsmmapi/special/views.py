from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, TemplateView, ListView

from ..custom.select_model import find_PBSMM_model
PBSMMSpecial = find_PBSMM_model('CUSTOM_PBSMM_SPECIAL_MODEL')

from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin
from pbsmmapi.abstract.mixin_helpers import filter_offline_shows, filter_offline_parent_show

class PBSMMAllSpecialListView(ListView, PBSMMObjectListMixin):
    model = PBSMMSpecial
    template_name = 'special/special_list.html'
    context_object_name = 'special_list'
    
    def get_queryset(self):
        qs = super(PBSMMAllSpecialListView, self).get_queryset()
        qs = filter_offline_shows(qs, self.request.user.is_authenticated)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMAllSpecialListView, self).get_context_data(**kwargs)
        return context
        
class PBSMMShowSpecialListView(ListView, PBSMMObjectListMixin):
    model = PBSMMSpecial
    template_name = 'special/special_list.html'
    context_object_name = 'special_list'
    
    def get_queryset(self):
        qs = super(PBSMMShowSpecialListView, self).get_queryset()
        show_slug = self.kwargs['show_slug']
        qs = qs.filter(show__slug=show_slug)
        qs = filter_offline_shows(qs, self.request.user.is_authenticated)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMShowSpecialListView, self).get_context_data(**kwargs)
        return context
        
class PBSMMSpecialDetailView(DetailView, PBSMMObjectDetailMixin):
    model = PBSMMSpecial
    template_name = 'special/special_detail.html'
    context_object_name = 'special'
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMSpecialDetailView, self).get_context_data(**kwargs)
        return context
        