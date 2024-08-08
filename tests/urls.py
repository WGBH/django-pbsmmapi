from django.conf.urls import (
    include,
    url,
)

urlpatterns = [url("shows/", include("pbsmmapi.show.urls"))]
