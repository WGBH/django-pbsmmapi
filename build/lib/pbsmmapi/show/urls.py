from django.conf.urls import url
from .views import PBSMMShowListView, PBSMMShowDetailView

urlpatterns = (
    url(r'^$', PBSMMShowListView.as_view(), name='show-list'),
    url(r'^(?P<slug>[^/]+)/$',
        PBSMMShowDetailView.as_view(),
        name='show-detail'),
)
