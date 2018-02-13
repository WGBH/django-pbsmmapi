from django.forms import ModelForm

from .models import PBSMMCollection

class PBSMMCollectionCreateForm(ModelForm):

    class Meta:
        model = PBSMMCollection
        fields = (
            'object_id',
        )

class PBSMMCollectionEditForm(ModelForm):

    class Meta:
        model = PBSMMCollection
        exclude = []
