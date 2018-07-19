from django.forms import ModelForm
from ..custom.select_model import find_PBSMM_model

PBSMMSpecial = find_PBSMM_model('CUSTOM_PBSMM_EPISODE_MODEL')

class PBSMMSpecialCreateForm(ModelForm):

    class Meta:
        model = PBSMMSpecial
        fields = (
            'slug', 'show'
        )

class PBSMMSpecialEditForm(ModelForm):

    class Meta:
        model = PBSMMSpecial
        exclude = []
