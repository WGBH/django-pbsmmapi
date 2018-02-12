from django.forms import ModelForm

from .models import PBSMMRemoteAsset

class PBSMMRemoteAssetCreateForm(ModelForm):

    class Meta:
        model = PBSMMRemoteAsset
        fields = (
            'object_id',
        )

class PBSMMRemoteAssetEditForm(ModelForm):

    class Meta:
        model = PBSMMRemoteAsset
        exclude = []
