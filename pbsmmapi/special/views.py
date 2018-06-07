from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, TemplateView, ListView

from pbsmmapi.special.models import PBSMMSpecial as Special
from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin
from pbsmmapi.abstract.mixin_helpers import filter_offline_shows, filter_offline_parent_show

class PBSMMSpecialListView(ListView, PBSMMObjectListMixin):
    model = Special
    template_name = 'special/special_list.html'
    context_object_name = 'special_list'
    
    def get_queryset(self):
        qs = super(PBSMMSpecialListView, self).get_queryset()
        qs = filter_offline_shows(qs, self.request.user.is_authenticated)
        return qs
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMSpecialListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['login'] = True
        else:
            context['login'] = False
        return context

        
class PBSMMSpecialDetailView(DetailView, PBSMMObjectDetailMixin):
    model = Special
    template_name = 'special/special_detail.html'
    context_object_name = 'special'
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMSpecialDetailView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated:
            context['login'] = True
        else:
            context['login'] = False
        return context
        