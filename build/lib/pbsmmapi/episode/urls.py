from django.conf.urls import url
from .views import PBSMMAllEpisodeListView, PBSMMSeasonEpisodeListView, PBSMMEpisodeDetailView

# For now assume there is an Episode listing page, and an Episode detail page.
#
# What we PROBABLY need is an Episode Listing Page FOR the subset of
# Episodes with common Show + Season.

urlpatterns = (
    url(r'^$', PBSMMAllEpisodeListView.as_view(), name='all-episode-list'),
    url(r'^(?P<show_slug>[^/]+)/(?P<season_ordinal>[^/]+)/',
        PBSMMSeasonEpisodeListView.as_view(),
        name='season-episode-list'),
    url(r'^(?P<slug>[^/]+)/$',
        PBSMMEpisodeDetailView.as_view(),
        name='episode-detail'),
)
