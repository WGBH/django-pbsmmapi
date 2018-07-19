from django.forms import ModelForm
from pbsmmapi.show import get_show_model

PBSMMShow = get_show_model()

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
