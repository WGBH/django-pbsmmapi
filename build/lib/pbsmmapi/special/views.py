from django.views.generic import DetailView, ListView

from pbsmmapi.special.models import PBSMMSpecial as Special
from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin
from pbsmmapi.abstract.mixin_helpers import filter_offline_shows


class PBSMMAllSpecialListView(ListView, PBSMMObjectListMixin):
    model = Special
    template_name = 'special/special_list.html'
    context_object_name = 'special_list'

    def get_queryset(self):
        qs = super(PBSMMAllSpecialListView, self).get_queryset()
        qs = filter_offline_shows(qs, self.request.user.is_authenticated)
        return qs

    def get_context_data(self, **kwargs):
        context = super(
            PBSMMAllSpecialListView,
            self).get_context_data(
            **kwargs)
        return context


class PBSMMShowSpecialListView(ListView, PBSMMObjectListMixin):
    model = Special
    template_name = 'special/special_list.html'
    context_object_name = 'special_list'

    def get_queryset(self):
        qs = super(PBSMMShowSpecialListView, self).get_queryset()
        show_slug = self.kwargs['show_slug']
        qs = qs.filter(show__slug=show_slug)
        qs = filter_offline_shows(qs, self.request.user.is_authenticated)
        return qs

    def get_context_data(self, **kwargs):
        context = super(
            PBSMMShowSpecialListView,
            self).get_context_data(
            **kwargs)
        return context


class PBSMMSpecialDetailView(DetailView, PBSMMObjectDetailMixin):
    model = Special
    template_name = 'special/special_detail.html'
    context_object_name = 'special'

    def get_context_data(self, **kwargs):
        context = super(
            PBSMMSpecialDetailView,
            self).get_context_data(
            **kwargs)
        return context
