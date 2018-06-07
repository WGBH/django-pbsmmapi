from django.conf.urls import url
from .views import PBSMMSpecialListView, PBSMMSpecialDetailView

urlpatterns = (
    url(r'^$', PBSMMSpecialListView.as_view(), name='special-list'),
    url(r'^(?P<slug>[^/]+)/$', PBSMMSpecialDetailView.as_view(), name='special-detail'),
)