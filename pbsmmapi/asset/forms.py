from django.forms import ModelForm

from .models import PBSMMAsset

class PBSMMAssetCreateForm(ModelForm):

    class Meta:
        model = PBSMMAsset
        fields = (
            'object_id',
            'legacy_tp_media_id'
        )

class PBSMMAssetEditForm(ModelForm):

    class Meta:
        model = PBSMMAsset
        exclude = []
