from django import forms 
from django.conf import settings
from importlib import import_module

if settings.CUSTOM_PBSMM_EPISODE_MODEL:
    module_model = settings.CUSTOM_PBSMM_EPISODE_MODEL.split('.')
    module = import_module(module_model[0])
    model = getattr(module, module_model[1])
    PBSMMEpisode = model
else:
    from ..pure.models import PBSMMEpisode

class PBSMMEpisodeCreateForm(forms.ModelForm):
    """
    This overrides the Admin form when creating an Episode (by hand).
    Usually Episodes are "created" when ingesting a parental Season
    (or a grand-parental Show).
    """
    class Meta:
        model = PBSMMEpisode
        fields = ('slug', 'season')

class PBSMMEpisodeEditForm(forms.ModelForm):

    class Meta:
        model = PBSMMEpisode
        exclude = []
