from django.forms import ModelForm
from django.conf import settings
from importlib import import_module

if settings.CUSTOM_PBSMM_SEASON_MODEL:
    module_model = settings.CUSTOM_PBSMM_SEASON_MODEL.split('.')
    module = import_module(module_model[0])
    model = getattr(module, module_model[1])
    PBSMMSeason = model
else:
    from ..pure.models import PBSMMSeason

class PBSMMSeasonCreateForm(ModelForm):
    """
    Override the Model form so that only these two fields show up.
    This is for adding a Season "by hand" although in general, they will
    be created as part of the process of seeding a Show.
    """
    class Meta:
        model = PBSMMSeason
        fields = (
            'object_id', 'show'
        )

class PBSMMSeasonEditForm(ModelForm):

    class Meta:
        model = PBSMMSeason
        exclude = []
