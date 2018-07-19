from django.forms import ModelForm
from pbsmmapi.special import get_special_model

PBSMMSpecial = get_special_model()

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
