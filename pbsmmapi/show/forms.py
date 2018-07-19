from django.forms import ModelForm
from django.conf import settings
from importlib import import_module

if settings.CUSTOM_PBSMM_SHOW_MODEL:
    module_model = settings.CUSTOM_PBSMM_SHOW_MODEL.split('.')
    module = import_module(module_model[0])
    model = getattr(module, module_model[1])
    PBSMMShow = model
else:
    from ..pure.models import PBSMMShow

class PBSMMShowCreateForm(ModelForm):
    """
    """
    class Meta:
        model = PBSMMShow
        fields = (
            'slug', 'title', 
            'ingest_seasons', 'ingest_specials', 'ingest_episodes',
        )

class PBSMMShowEditForm(ModelForm):

    class Meta:
        model = PBSMMShow
        exclude = []
