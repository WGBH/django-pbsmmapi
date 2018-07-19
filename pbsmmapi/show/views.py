from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, TemplateView, ListView

from ..custom.select_model import find_PBSMM_model
PBSMMShow = find_PBSMM_model('CUSTOM_PBSMM_SHOW_MODEL')

from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin

class PBSMMShowListView(ListView, PBSMMObjectListMixin):
    model = PBSMMShow
    template_name = 'show/show_list.html'
    context_object_name = 'show_list'
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMShowListView, self).get_context_data(**kwargs)
        return context

        
class PBSMMShowDetailView(DetailView, PBSMMObjectDetailMixin):
    model = PBSMMShow
    template_name = 'show/show_detail.html'
    context_object_name = 'show'
    
    def get_context_data(self, **kwargs):
        context = super(PBSMMShowDetailView, self).get_context_data(**kwargs)
        return context
        