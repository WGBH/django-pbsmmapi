from django.conf.urls import url, include


urlpatterns = [
    url('shows/', include('pbsmmapi.show.urls'))
]
