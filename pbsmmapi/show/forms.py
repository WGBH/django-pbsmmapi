from django.forms import ModelForm
from ..custom.select_model import find_PBSMM_model

PBSMMShow = find_PBSMM_model('CUSTOM_PBSMM_SHOW_MODEL')

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
