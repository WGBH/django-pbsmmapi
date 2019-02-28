from django.forms import ModelForm

from .models import PBSMMShow


class PBSMMShowCreateForm(ModelForm):
    """
    """
    class Meta:
        model = PBSMMShow
        fields = (
            'slug', 'title',
            'ingest_seasons', 'ingest_specials', 'ingest_episodes',
        )


class PBSMMShowEditForm(ModelForm):
    class Meta:
        model = PBSMMShow
        exclude = []
