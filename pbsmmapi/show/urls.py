from django.conf.urls import url

from .views import (
    PBSMMShowDetailView,
    PBSMMShowListView,
)

urlpatterns = (
    url(r"^$", PBSMMShowListView.as_view(), name="show-list"),
    url(r"^(?P<slug>[^/]+)/$", PBSMMShowDetailView.as_view(), name="show-detail"),
)
