from django.forms import ModelForm
from django.conf import settings
from importlib import import_module

if settings.CUSTOM_PBSMM_SPECIAL_MODEL:
    module_model = settings.CUSTOM_PBSMM_SPECIAL_MODEL.split('.')
    module = import_module(module_model[0])
    model = getattr(module, module_model[1])
    PBSMMSpecial = model
else:
    from ..pure.models import PBSMMSpecial

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
