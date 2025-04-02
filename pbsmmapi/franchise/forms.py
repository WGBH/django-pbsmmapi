from django.forms import ModelForm

from pbsmmapi.franchise.models import Franchise


class PBSMMFranchiseCreateForm(ModelForm):
    class Meta:
        model = Franchise
        fields = (
            "slug",
            "title",
            "ingest_shows",
            "ingest_seasons",
            "ingest_specials",
            "ingest_episodes",
        )


class PBSMMFranchiseEditForm(ModelForm):
    class Meta:
        model = Franchise
        exclude = []
