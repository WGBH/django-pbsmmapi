from django.conf.urls import url

from pbsmmapi.show.views import PBSMMShowDetailView
from pbsmmapi.show.views import PBSMMShowListView

urlpatterns = (
    url(r'^$', PBSMMShowListView.as_view(), name='show-list'),
    url(r'^(?P<slug>[^/]+)/$', PBSMMShowDetailView.as_view(), name='show-detail'),
)
