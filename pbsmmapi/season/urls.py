from django.conf.urls import url
from .views import PBSMMSeasonListView, PBSMMSeasonDetailView

##### For now, allow for a Season Listing Page.
#####   This will probably be replaced by a page that lists the Seasons for a given Show.
#####
##### Hoever, also allow for an Season Detail Page.
urlpatterns = (
    url(r'^$', PBSMMSeasonListView.as_view(), name='season-list'),
    url(r'^(?P<ordinal>[^/]+)/$', PBSMMSeasonDetailView.as_view(), name='season-detail'),
)