from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render
from django.views.generic import DetailView, TemplateView, ListView
from importlib import import_module

if settings.CUSTOM_PBSMM_SHOW_MODEL:
    module_model = settings.CUSTOM_PBSMM_SHOW_MODEL.split('.')
    module = import_module(module_model[0])
    model = getattr(module, module_model[1])
    PBSMMShow = model
else:
    from ..pure.models import PBSMMShow

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
        