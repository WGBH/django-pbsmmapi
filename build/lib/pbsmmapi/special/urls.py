from django.conf.urls import url
from .views import PBSMMAllSpecialListView, PBSMMShowSpecialListView, PBSMMSpecialDetailView

urlpatterns = (
    url(r'^$', PBSMMAllSpecialListView.as_view(), name='all-special-list'),
    url(r'^show/(?P<show_slug>[^/]+/)',
        PBSMMShowSpecialListView.as_view(),
        name='show-special-list'),
    url(r'^(?P<slug>[^/]+)/$',
        PBSMMSpecialDetailView.as_view(),
        name='special-detail'),
)
