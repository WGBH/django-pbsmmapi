from django.conf.urls import url
from .views import PBSMMEpisodeListView, PBSMMEpisodeDetailView

# For now assume there is an Episode listing page, and an Episode detail page.
#
# What we PROBABLY need is an Episode Listing Page FOR the subset of Episodes with common Show + Season.
#
urlpatterns = (
    url(r'^$', PBSMMEpisodeListView.as_view(), name='episode-list'),
    url(r'^(?P<slug>[^/]+)/$', PBSMMEpisodeDetailView.as_view(), name='episode-detail'),
)