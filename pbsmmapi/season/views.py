from django.views.generic import DetailView, ListView

from pbsmmapi.season.models import PBSMMSeason as Season
from pbsmmapi.show.models import PBSMMShow as Show
from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin
from pbsmmapi.abstract.mixin_helpers import filter_offline_shows


class PBSMMAllSeasonListView(ListView, PBSMMObjectListMixin):
    """
    This is the Season Listing View - it's generic and is Show agnostic.
    Gate-keeping is handled in the PBSMMObjectListMixin class.
    """
    model = Season
    template_name = 'season/season_list.html'
    context_object_name = 'season_list'

    def get_queryset(self):
        qs = super(PBSMMAllSeasonListView, self).get_queryset()
        qs = filter_offline_shows(qs, self.request.user)
        return qs

    def get_context_data(self, **kwargs):
        context = super(
            PBSMMAllSeasonListView,
            self).get_context_data(
            **kwargs)
        context['all_seasons'] = True
        return context


class PBSMMShowSeasonListView(ListView, PBSMMObjectListMixin):
    """
    This is the subset of Seasons for a given show.
    Gate-keeping is handled in the PBSMObjectListMixin class.
    """
    model = Season
    template_name = 'season/season_list.html'
    context_object_name = 'season_list'

    def get_queryset(self):
        qs = super(PBSMMShowSeasonListView, self).get_queryset()
        show_slug = self.kwargs['show_slug']
        qs = qs.filter(show__slug=show_slug)
        return qs

    def get_context_data(self, **kwargs):
        context = super(
            PBSMMShowSeasonListView,
            self).get_context_data(
            **kwargs)
        context['all_seasons'] = False
        context['parent_show'] = Show.objects.get(
            slug=self.kwargs['show_slug'])
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
