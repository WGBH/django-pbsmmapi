from django.forms import ModelForm

from .models import PBSMMShow

class PBSMMShowCreateForm(ModelForm):

    class Meta:
        model = PBSMMShow
        fields = (
            'object_id',
        )

class PBSMMShowEditForm(ModelForm):

    class Meta:
        model = PBSMMShow
        exclude = []
