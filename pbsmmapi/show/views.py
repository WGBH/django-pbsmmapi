from django.views.generic import DetailView
from django.views.generic import ListView

from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin
from pbsmmapi.abstract.mixins import PBSMMObjectListMixin
from pbsmmapi.show.models import PBSMMShow as Show


class PBSMMShowListView(ListView, PBSMMObjectListMixin):
    model = Show
    template_name = 'show/show_list.html'
    context_object_name = 'show_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class PBSMMShowDetailView(DetailView, PBSMMObjectDetailMixin):
    model = Show
    template_name = 'show/show_detail.html'
    context_object_name = 'show'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
