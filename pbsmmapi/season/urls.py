from django.conf.urls import url

from pbsmmapi.season.views import PBSMMAllSeasonListView
from pbsmmapi.season.views import PBSMMSeasonDetailView
from pbsmmapi.season.views import PBSMMShowSeasonListView

# For now, allow for a Season Listing Page.
# This will probably be replaced by a page that lists the Seasons for a given Show.
#
# Hoever, also allow for an Season Detail Page.
urlpatterns = (
    url(
        r'^$',
        PBSMMAllSeasonListView.as_view(),
        name='all-season-list',
    ),
    url(
        r'^show/(?P<show_slug>[^/]+)/$',
        PBSMMShowSeasonListView.as_view(),
        name='show-season-list',
    ),
    url(
        r'^(?P<pk>[^/]+)/$',
        PBSMMSeasonDetailView.as_view(),
        name='season-detail',
    ),
)
