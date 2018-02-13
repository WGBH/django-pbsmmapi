from django.forms import ModelForm

from .models import PBSMMFranchise

class PBSMMFranchiseCreateForm(ModelForm):

    class Meta:
        model = PBSMMFranchise
        fields = (
            'object_id',
        )

class PBSMMFranchiseEditForm(ModelForm):

    class Meta:
        model = PBSMMFranchise
        exclude = []
