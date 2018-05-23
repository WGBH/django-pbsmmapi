from django.forms import ModelForm

from .models import PBSMMSpecial

class PBSMMSpecialCreateForm(ModelForm):

    class Meta:
        model = PBSMMSpecial
        fields = (
            'object_id', 'show'
        )

class PBSMMSpecialEditForm(ModelForm):

    class Meta:
        model = PBSMMSpecial
        exclude = []
