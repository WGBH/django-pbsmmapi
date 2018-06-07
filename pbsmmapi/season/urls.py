from django.conf.urls import url
from .views import PBSMMSeasonListView, PBSMMSeasonDetailView

urlpatterns = (
    url(r'^$', PBSMMSeasonListView.as_view(), name='season-list'),
    url(r'^(?P<ordinal>[^/]+)/$', PBSMMSeasonDetailView.as_view(), name='season-detail'),
)