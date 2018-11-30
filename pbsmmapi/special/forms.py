from django.forms import ModelForm

from .models import PBSMMSpecial


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
