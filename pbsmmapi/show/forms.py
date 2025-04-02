from django.forms import ModelForm

from pbsmmapi.show.models import Show


class PBSMMShowCreateForm(ModelForm):
    class Meta:
        model = Show
        fields = (
            "slug",
            "title",
            "ingest_seasons",
            "ingest_specials",
            "ingest_episodes",
        )


class PBSMMShowEditForm(ModelForm):
    class Meta:
        model = Show
        exclude = []
