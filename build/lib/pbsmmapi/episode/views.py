from django.views.generic import DetailView, ListView

from pbsmmapi.abstract.mixins import PBSMMObjectDetailMixin, PBSMMObjectListMixin
from pbsmmapi.abstract.mixin_helpers import filter_offline_seasons, filter_offline_parent_season
from pbsmmapi.episode.models import PBSMMEpisode as Episode


class PBSMMAllEpisodeListView(ListView, PBSMMObjectListMixin):
    """
    This is the Episode Listing View - it's generic and is Show/Season agnostic.
    Gate-keeping is handled in the PBSMMObjectListMixin class.
    """
    model = Episode
    template_name = 'episode/episode_list.html'
    context_object_name = 'episode_list'

    def get_queryset(self):
        """
        Back-filter the queryset for parental Season (and grand-parental Show).
        """
        qs = super(PBSMMAllEpisodeListView, self).get_queryset()
        qs = filter_offline_seasons(qs, self.request.user.is_authenticated)
        return qs


class PBSMMSeasonEpisodeListView(ListView, PBSMMObjectListMixin):
    """
    This is the Episode Listing View - it's generic and is Show/Season agnostic.
    Gate-keeping is handled in the PBSMMObjectListMixin class.
    """
    model = Episode
    template_name = 'episode/episode_list.html'
    context_object_name = 'episode_list'

    def get_queryset(self):
        """
        Back-filter the queryset for parental Season (and grand-parental Show).
        """
        qs = super(PBSMMSeasonEpisodeListView, self).get_queryset()
        # Filter out the grandparent show
        show_slug = self.kwargs['show_slug']
        qs = qs.filter(season__show__slug=show_slug)
        # Filter out the parent season
        season_ordinal = self.kwargs['season_ordinal']
        qs = qs.filter(season__ordinal=season_ordinal)
        # filter out offline parental seasons
        qs = filter_offline_seasons(qs, self.request.user.is_authenticated)
        return qs


class PBSMMEpisodeDetailView(DetailView, PBSMMObjectDetailMixin):
    """
    This is the Episode detail view.
    Gate-keeping is handled in the PBSMMObjectDetailMixin class.
    """
    model = Episode
    template_name = 'episode/episode_detail.html'
    context_object_name = 'episode'

    def get_object(self, queryset=None):
        """
        Back filter the Episode's parental Season and grand-parental Show
        """
        obj = super(PBSMMEpisodeDetailView, self).get_object(queryset=queryset)
        obj = filter_offline_parent_season(obj, self.request.user)
        return obj

    def get_context_data(self, **kwargs):
        context = super(
            PBSMMEpisodeDetailView,
            self).get_context_data(
            **kwargs)
        return context
