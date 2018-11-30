from django.views.generic import DetailView, ListView

from pbsmmapi.show.models import PBSMMShow as Show
from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin


class PBSMMShowListView(ListView, PBSMMObjectListMixin):
    model = Show
    template_name = 'show/show_list.html'
    context_object_name = 'show_list'

    def get_context_data(self, **kwargs):
        context = super(PBSMMShowListView, self).get_context_data(**kwargs)
        return context


class PBSMMShowDetailView(DetailView, PBSMMObjectDetailMixin):
    model = Show
    template_name = 'show/show_detail.html'
    context_object_name = 'show'

    def get_context_data(self, **kwargs):
        context = super(PBSMMShowDetailView, self).get_context_data(**kwargs)
        return context
